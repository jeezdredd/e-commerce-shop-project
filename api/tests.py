from decimal import Decimal

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from catalog.models import Category, Product, Review, Tag
from orders.models import DeliverySettings, Order, OrderItem
from payments.models import Payment
from payments.tasks import process_payment


class CatalogTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(title="Электроника")
        self.tag = Tag.objects.create(name="Gaming")
        self.cheap = Product.objects.create(
            category=self.category, title="Мышь", price=Decimal("500"), count=10,
            sort_index=1, purchases_count=5,
        )
        self.expensive = Product.objects.create(
            category=self.category, title="Ноутбук", price=Decimal("90000"), count=3,
            sort_index=0, purchases_count=50, limited_edition=True,
        )
        self.expensive.tags.add(self.tag)

    def test_catalog_filter_by_name(self):
        resp = self.client.get("/api/catalog/", {"filter[name]": "ноут"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        titles = [item["title"] for item in resp.json()["items"]]
        self.assertEqual(titles, ["Ноутбук"])

    def test_catalog_filter_by_price(self):
        resp = self.client.get(
            "/api/catalog/", {"filter[minPrice]": "1000", "filter[maxPrice]": "100000"}
        )
        titles = [item["title"] for item in resp.json()["items"]]
        self.assertEqual(titles, ["Ноутбук"])

    def test_catalog_sort_price_inc(self):
        resp = self.client.get("/api/catalog/", {"sort": "price", "sortType": "inc"})
        titles = [item["title"] for item in resp.json()["items"]]
        self.assertEqual(titles, ["Мышь", "Ноутбук"])

    def test_popular_orders_by_sort_index(self):
        resp = self.client.get("/api/products/popular/")
        titles = [item["title"] for item in resp.json()]
        self.assertEqual(titles[0], "Ноутбук")

    def test_limited_only_limited_edition(self):
        resp = self.client.get("/api/products/limited/")
        titles = [item["title"] for item in resp.json()]
        self.assertEqual(titles, ["Ноутбук"])


class BasketTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(title="Cat")
        self.product = Product.objects.create(
            category=self.category, title="Item", price=Decimal("100"), count=10
        )

    def test_add_and_remove(self):
        resp = self.client.post(
            "/api/basket/", {"id": self.product.id, "count": 2}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()[0]["count"], 2)

        resp = self.client.delete(
            "/api/basket/", {"id": self.product.id, "count": 1}, format="json"
        )
        self.assertEqual(resp.json()[0]["count"], 1)


class OrderTests(APITestCase):
    def setUp(self):
        DeliverySettings.objects.get_or_create(pk=1)
        self.category = Category.objects.create(title="Cat")
        self.product = Product.objects.create(
            category=self.category, title="Item", price=Decimal("1000"), count=10
        )
        self.user = User.objects.create_user(
            username="buyer", password="123456", email="b@b.ru", full_name="Buyer"
        )

    def test_create_order_with_delivery_cost(self):
        self.client.force_authenticate(self.user)
        self.client.post(
            "/api/basket/", {"id": self.product.id, "count": 1}, format="json"
        )
        resp = self.client.post("/api/orders/", [], format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        order = Order.objects.get(pk=resp.json()["orderId"])
        self.assertEqual(order.products_cost(), Decimal("1000"))
        self.assertEqual(order.delivery_cost(), Decimal("200"))
        self.assertEqual(order.total_cost, Decimal("1200"))

    def test_free_delivery_over_threshold(self):
        self.client.force_authenticate(self.user)
        self.client.post(
            "/api/basket/", {"id": self.product.id, "count": 3}, format="json"
        )
        resp = self.client.post("/api/orders/", [], format="json")
        order = Order.objects.get(pk=resp.json()["orderId"])
        self.assertEqual(order.delivery_cost(), 0)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class PaymentTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(title="Cat")
        self.product = Product.objects.create(
            category=self.category, title="Item", price=Decimal("100"), count=10
        )
        self.order = Order.objects.create(status=Order.STATUS_ACCEPTED)
        OrderItem.objects.create(
            order=self.order, product=self.product, count=1, price=Decimal("100")
        )

    def test_odd_number_rejected(self):
        resp = self.client.post(
            f"/api/payment/{self.order.id}/", {"number": "1111111"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_masked_card_accepted(self):
        resp = self.client.post(
            f"/api/payment/{self.order.id}/",
            {"number": "1234 5678 1234 5678"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_even_not_zero_confirmed(self):
        payment = Payment.objects.create(order=self.order, number="1234")
        process_payment(payment.id)
        payment.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(payment.status, Payment.STATUS_CONFIRMED)
        self.assertEqual(self.order.status, Order.STATUS_PAID)

    def test_even_ending_zero_error(self):
        payment = Payment.objects.create(order=self.order, number="1230")
        process_payment(payment.id)
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.STATUS_ERROR)
        self.assertTrue(payment.error_text)


class ProfileTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="u1", password="123456", email="u1@u.ru",
            phone="111", full_name="User One",
        )
        self.other = User.objects.create_user(
            username="u2", password="123456", email="u2@u.ru", phone="222"
        )

    def test_email_must_be_unique(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            "/api/profile/",
            {"fullName": "User One", "email": "u2@u.ru", "phone": "111"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class SoftDeleteTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(title="Cat")
        self.product = Product.objects.create(
            category=self.category, title="Item", price=Decimal("100"), count=1
        )

    def test_soft_delete_hides_from_default_manager(self):
        self.product.delete()
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())
        self.assertTrue(Product.all_objects.filter(pk=self.product.pk).exists())
        self.product.restore()
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())


class ReviewTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(title="Cat")
        self.product = Product.objects.create(
            category=self.category, title="Item", price=Decimal("100"), count=1
        )
        self.user = User.objects.create_user(
            username="r1", password="123456", email="r1@r.ru"
        )

    def test_review_requires_auth(self):
        resp = self.client.post(
            f"/api/product/{self.product.id}/reviews/",
            {"author": "A", "email": "a@a.ru", "text": "ok", "rate": 5},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_review_created(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            f"/api/product/{self.product.id}/reviews/",
            {"author": "A", "email": "a@a.ru", "text": "ok", "rate": 5},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Review.objects.count(), 1)
