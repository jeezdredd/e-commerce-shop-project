import json

from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from cart.services import CartService
from catalog.models import Category, Product, Sale, Tag
from orders.models import Order, OrderItem
from payments.models import Payment
from payments.tasks import process_payment

from .serializers import (
    CategorySerializer,
    OrderSerializer,
    ProductFullSerializer,
    ProductShortSerializer,
    ReviewSerializer,
    SaleSerializer,
    TagSerializer,
)

PAGE_SIZE = 20


def basket_payload(cart):
    data = []
    for product, count in cart.products():
        item = ProductShortSerializer(product).data
        item["count"] = count
        data.append(item)
    return data


class SignInView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        payload = json.loads(request.body or "{}")
        user = authenticate(
            request,
            username=payload.get("username"),
            password=payload.get("password"),
        )
        if user is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        login(request, user)
        CartService(request).merge_session_into_user()
        return Response(status=status.HTTP_200_OK)


class SignUpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return Response(
                {"error": "Некорректный формат запроса"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        username = (payload.get("username") or "").strip()
        password = payload.get("password") or ""
        name = payload.get("name") or ""
        if not username or not password:
            return Response(
                {"error": "Логин и пароль обязательны"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.all_objects.filter(username=username).exists():
            return Response(
                {"error": "Пользователь с таким логином уже существует"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            User.objects.create_user(
                username=username, password=password, full_name=name
            )
        except IntegrityError:
            return Response(
                {"error": "Не удалось создать пользователя, попробуйте другой логин"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = authenticate(request, username=username, password=password)
        login(request, user)
        CartService(request).merge_session_into_user()
        return Response(status=status.HTTP_200_OK)


class SignOutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_200_OK)


class CategoriesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Category.objects.filter(is_active=True, parent__isnull=True)
        return Response(CategorySerializer(qs, many=True).data)


class TagsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        category = request.query_params.get("category")
        qs = Tag.objects.all()
        if category:
            qs = qs.filter(products__category_id=category).distinct()
        return Response(TagSerializer(qs, many=True).data)


class CatalogView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        params = request.query_params
        qs = Product.objects.all()

        name = params.get("filter[name]") or params.get("name")
        if name:
            qs = qs.filter(title__icontains=name)
        min_price = params.get("filter[minPrice]")
        max_price = params.get("filter[maxPrice]")
        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)
        if params.get("filter[freeDelivery]") in ("true", "True", "1"):
            qs = qs.filter(free_delivery=True)
        if params.get("filter[available]") in ("true", "True", "1"):
            qs = qs.filter(count__gt=0)

        category = params.get("category")
        if category and category.isdigit():
            qs = qs.filter(
                Q(category_id=category) | Q(category__parent_id=category)
            )

        tags = [
            t for t in (params.getlist("tags[]") or params.getlist("tags"))
            if str(t).isdigit()
        ]
        if tags:
            qs = qs.filter(tags__id__in=tags).distinct()

        qs = qs.annotate(
            _rating=Avg("reviews__rate"), _reviews=Count("reviews", distinct=True)
        )

        sort = params.get("sort", "date")
        sort_type = params.get("sortType", "dec")
        sort_map = {
            "rating": "purchases_count",
            "price": "price",
            "reviews": "_reviews",
            "date": "date",
        }
        field = sort_map.get(sort, "date")
        prefix = "-" if sort_type == "dec" else ""
        qs = qs.order_by(f"{prefix}{field}")

        try:
            limit = int(params.get("limit", PAGE_SIZE))
        except (TypeError, ValueError):
            limit = PAGE_SIZE
        try:
            current_page = int(params.get("currentPage", 1))
        except (TypeError, ValueError):
            current_page = 1

        total = qs.count()
        last_page = max(1, (total + limit - 1) // limit)
        start = (current_page - 1) * limit
        page_items = qs[start:start + limit]

        return Response(
            {
                "items": ProductShortSerializer(page_items, many=True).data,
                "currentPage": current_page,
                "lastPage": last_page,
            }
        )


class PopularProductsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Product.objects.order_by("sort_index", "-purchases_count")[:8]
        return Response(ProductShortSerializer(qs, many=True).data)


class LimitedProductsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Product.objects.filter(limited_edition=True)[:16]
        return Response(ProductShortSerializer(qs, many=True).data)


class BannersView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Product.objects.filter(is_banner=True)[:3]
        return Response(ProductShortSerializer(qs, many=True).data)


class SalesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            current_page = int(request.query_params.get("currentPage", 1))
        except (TypeError, ValueError):
            current_page = 1
        qs = Sale.objects.select_related("product").all()
        total = qs.count()
        last_page = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        start = (current_page - 1) * PAGE_SIZE
        page_items = qs[start:start + PAGE_SIZE]
        return Response(
            {
                "items": SaleSerializer(page_items, many=True).data,
                "currentPage": current_page,
                "lastPage": last_page,
            }
        )


class ProductDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        return Response(ProductFullSerializer(product).data)


class ProductReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ReviewSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save(product=product)
        reviews = product.reviews.all()
        return Response(ReviewSerializer(reviews, many=True).data)


class BasketView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(basket_payload(CartService(request)))

    def post(self, request):
        cart = CartService(request)
        cart.add(request.data.get("id"), request.data.get("count", 1))
        return Response(basket_payload(cart))

    def delete(self, request):
        cart = CartService(request)
        payload = request.data
        if isinstance(payload, (bytes, str)):
            payload = json.loads(payload or "{}")
        cart.remove(payload.get("id"), payload.get("count"))
        return Response(basket_payload(cart))


class OrdersView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response([])
        orders = Order.objects.filter(user=request.user)
        return Response(OrderSerializer(orders, many=True).data)

    def post(self, request):
        cart = CartService(request)
        products = cart.products()
        if not products:
            return Response(
                {"error": "empty cart"}, status=status.HTTP_400_BAD_REQUEST
            )
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
        )
        if request.user.is_authenticated:
            order.full_name = request.user.full_name
            order.email = request.user.email
            order.phone = request.user.phone or ""
        for product, count in products:
            OrderItem.objects.create(
                order=order, product=product, count=count, price=product.price
            )
        order.recalculate_total()
        order.save()
        return Response({"orderId": order.id})


class OrderDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        return Response(OrderSerializer(order).data)

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        data = request.data
        order.full_name = data.get("full_name", order.full_name)
        order.email = data.get("email", order.email)
        order.phone = data.get("phone", order.phone)
        order.delivery_type = data.get("delivery_type", order.delivery_type)
        order.payment_type = data.get("payment_type", order.payment_type)
        order.city = data.get("city", order.city)
        order.address = data.get("address", order.address)
        order.status = Order.STATUS_ACCEPTED
        if request.user.is_authenticated and order.user is None:
            order.user = request.user
        order.recalculate_total()
        order.save()
        CartService(request).clear()
        return Response({"orderId": order.id})


class PaymentView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        raw_number = str(request.data.get("number", ""))
        number = "".join(ch for ch in raw_number if ch.isdigit())
        if not number or int(number) % 2 != 0:
            return Response(
                {"error": "Invalid card number"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        payment = Payment.objects.create(
            order=order,
            number=number,
            name=request.data.get("name", ""),
            month=request.data.get("month", ""),
            year=request.data.get("year", ""),
            code=request.data.get("code", ""),
        )
        process_payment.delay(payment.id)
        return Response(status=status.HTTP_200_OK)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(self._serialize(request.user))

    def post(self, request):
        user = request.user
        user.full_name = request.data.get("full_name", user.full_name)
        email = request.data.get("email", user.email)
        phone = request.data.get("phone", user.phone)
        if email and User.objects.filter(email=email).exclude(pk=user.pk).exists():
            return Response(
                {"error": "email exists"}, status=status.HTTP_400_BAD_REQUEST
            )
        if phone and User.objects.filter(phone=phone).exclude(pk=user.pk).exists():
            return Response(
                {"error": "phone exists"}, status=status.HTTP_400_BAD_REQUEST
            )
        user.email = email
        user.phone = phone
        user.save()
        return Response(self._serialize(user))

    @staticmethod
    def _serialize(user):
        avatar = (
            {"src": user.avatar.url, "alt": user.full_name}
            if user.avatar
            else None
        )
        return {
            "fullName": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "avatar": avatar,
        }


class ProfilePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        password = request.data.get("password")
        if not password:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        request.user.set_password(password)
        request.user.save()
        return Response(status=status.HTTP_200_OK)


class ProfileAvatarView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        avatar = request.FILES.get("avatar")
        if not avatar:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if avatar.size > 2 * 1024 * 1024:
            return Response(
                {"error": "Avatar too large"}, status=status.HTTP_400_BAD_REQUEST
            )
        request.user.avatar = avatar
        request.user.save()
        return Response({"src": request.user.avatar.url, "alt": request.user.full_name})


class AccountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        parts = (user.full_name or "").split()
        surname = parts[0] if len(parts) > 0 else ""
        firstname = parts[1] if len(parts) > 1 else ""
        secondname = parts[2] if len(parts) > 2 else ""
        avatar = (
            {"src": user.avatar.url, "alt": user.full_name}
            if user.avatar
            else None
        )
        orders = Order.objects.filter(user=user)
        return Response(
            {
                "firstname": firstname,
                "secondname": secondname,
                "surname": surname,
                "avatar": avatar,
                "orders": OrderSerializer(orders, many=True).data,
            }
        )
