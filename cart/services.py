from catalog.models import Product

from .models import Cart, CartItem

SESSION_KEY = "cart"


class CartService:
    def __init__(self, request):
        self.request = request
        self.user = request.user if request.user.is_authenticated else None

    def _session_cart(self):
        return self.request.session.setdefault(SESSION_KEY, {})

    def _save_session(self):
        self.request.session.modified = True

    def items(self):
        if self.user:
            cart, _ = Cart.objects.get_or_create(user=self.user)
            return {item.product_id: item.count for item in cart.items.all()}
        return {int(k): v for k, v in self._session_cart().items()}

    def add(self, product_id, count=1):
        product_id = int(product_id)
        count = int(count)
        if self.user:
            cart, _ = Cart.objects.get_or_create(user=self.user)
            item, created = CartItem.objects.get_or_create(
                cart=cart, product_id=product_id, defaults={"count": count}
            )
            if not created:
                item.count += count
                item.save(update_fields=["count"])
        else:
            data = self._session_cart()
            data[str(product_id)] = data.get(str(product_id), 0) + count
            self._save_session()

    def remove(self, product_id, count=None):
        product_id = int(product_id)
        if self.user:
            cart, _ = Cart.objects.get_or_create(user=self.user)
            try:
                item = cart.items.get(product_id=product_id)
            except CartItem.DoesNotExist:
                return
            if count is None or item.count <= count:
                item.delete()
            else:
                item.count -= count
                item.save(update_fields=["count"])
        else:
            data = self._session_cart()
            key = str(product_id)
            if key not in data:
                return
            if count is None or data[key] <= count:
                del data[key]
            else:
                data[key] -= count
            self._save_session()

    def clear(self):
        if self.user:
            Cart.objects.filter(user=self.user).delete()
        else:
            self.request.session[SESSION_KEY] = {}
            self._save_session()

    def merge_session_into_user(self):
        session_data = self.request.session.get(SESSION_KEY, {})
        if not session_data or not self.user:
            return
        cart, _ = Cart.objects.get_or_create(user=self.user)
        for pid, count in session_data.items():
            item, created = CartItem.objects.get_or_create(
                cart=cart, product_id=int(pid), defaults={"count": count}
            )
            if not created:
                item.count += count
                item.save(update_fields=["count"])
        self.request.session[SESSION_KEY] = {}
        self._save_session()

    def products(self):
        counts = self.items()
        products = Product.objects.filter(id__in=counts.keys())
        result = []
        for product in products:
            result.append((product, counts[product.id]))
        return result

    def total(self):
        return sum(product.price * count for product, count in self.products())
