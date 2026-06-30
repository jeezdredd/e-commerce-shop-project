import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from catalog.models import (
    Category,
    Product,
    ProductImage,
    Review,
    Sale,
    Specification,
    Tag,
)
from orders.models import Order, OrderItem

CUSTOMERS = [
    ("ivan", "Иванов Иван Иванович", "ivan@mail.ru", "89001112233"),
    ("petr", "Петров Пётр Петрович", "petr@mail.ru", "89004445566"),
    ("anna", "Сидорова Анна Сергеевна", "anna@mail.ru", "89007778899"),
]

DEFAULT_IMAGE = "products/card.jpg"

CATALOG = {
    "Электроника": {
        "icon": "categories/cat1.svg",
        "subcategories": {
            "Смартфоны": [
                ("Apple iPhone 15 128GB", 89990, "products/biggoods.png"),
                ("Samsung Galaxy S24 256GB", 79990, "products/biggoods.png"),
                ("Xiaomi 14 512GB", 64990, "products/biggoods.png"),
            ],
            "Ноутбуки": [
                ("Apple MacBook Air M3 13\"", 119990, "products/slider.png"),
                ("ASUS ZenBook 14 OLED", 84990, "products/slider.png"),
                ("Lenovo ThinkPad E14", 72990, "products/slider.png"),
            ],
            "Видеокарты": [
                ("NVIDIA GeForce RTX 4090", 159990, "products/videocard.png"),
                ("NVIDIA GeForce RTX 4070", 64990, "products/videocard.png"),
                ("AMD Radeon RX 7900 XTX", 89990, "products/videocard.png"),
            ],
        },
    },
    "Бытовая техника": {
        "icon": "categories/cat2.svg",
        "subcategories": {
            "Холодильники": [
                ("Bosch KGN39VL24R", 54990, "products/product.png"),
                ("Samsung RB37A5000", 49990, "products/product.png"),
                ("LG GA-B509CQWL", 47990, "products/product.png"),
            ],
            "Стиральные машины": [
                ("Bosch Serie 6 WAT", 42990, "products/product.png"),
                ("Samsung WW80T", 34990, "products/product.png"),
                ("Indesit BWSA 61051", 24990, "products/product.png"),
            ],
        },
    },
    "Аксессуары": {
        "icon": "categories/cat3.svg",
        "subcategories": {
            "Наушники": [
                ("Sony WH-1000XM5", 32990, "products/card.jpg"),
                ("Apple AirPods Pro 2", 24990, "products/card.jpg"),
                ("JBL Tune 720BT", 5990, "products/card.jpg"),
            ],
            "Чехлы": [
                ("Чехол Spigen для iPhone 15", 1990, "products/card.jpg"),
                ("Чехол Samsung Galaxy S24", 1490, "products/card.jpg"),
                ("Защитное стекло 2.5D", 590, "products/card.jpg"),
            ],
        },
    },
}

TAGS = ["Gaming", "Новинка", "Хит", "Скидка", "Премиум"]

CATEGORY_ICONS = ["categories/cat1.svg", "categories/cat2.svg", "categories/cat3.svg"]


class Command(BaseCommand):
    help = "Seed demo data (customers, categories, products, orders, sales)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Hard delete existing demo catalog/orders before seeding.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            OrderItem.objects.all().delete()
            Order.all_objects.all().hard_delete()
            Sale.objects.all().delete()
            Review.objects.all().delete()
            Specification.objects.all().delete()
            ProductImage.objects.all().delete()
            Product.all_objects.all().hard_delete()
            Category.all_objects.all().hard_delete()

        customer_group, _ = Group.objects.get_or_create(name="Customer")

        customers = []
        for username, full_name, email, phone in CUSTOMERS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"full_name": full_name, "email": email, "phone": phone},
            )
            if created:
                user.set_password("123456")
                user.save()
                user.groups.add(customer_group)
            customers.append(user)

        tags = [Tag.objects.get_or_create(name=name)[0] for name in TAGS]

        products = []
        for idx, (parent_title, parent_cfg) in enumerate(CATALOG.items()):
            parent, _ = Category.objects.get_or_create(
                title=parent_title,
                parent=None,
                defaults={
                    "is_active": True,
                    "is_favorite": idx < 3,
                    "sort_index": idx,
                    "icon": parent_cfg["icon"],
                },
            )
            for child_title, items in parent_cfg["subcategories"].items():
                child, _ = Category.objects.get_or_create(
                    title=child_title,
                    parent=parent,
                    defaults={"is_active": True},
                )
                for position, (title, price, image) in enumerate(items):
                    product, created = Product.objects.get_or_create(
                        title=title,
                        defaults={
                            "category": child,
                            "price": Decimal(price),
                            "count": random.randint(3, 40),
                            "description": f"{title} — официальная гарантия, доставка.",
                            "full_description": (
                                f"{title}. Подробное описание характеристик и "
                                f"комплектации товара."
                            ),
                            "free_delivery": price >= 30000,
                            "limited_edition": position == 0,
                            "is_banner": position == 0,
                            "sort_index": position,
                            "purchases_count": random.randint(0, 300),
                        },
                    )
                    if created:
                        product.tags.set(random.sample(tags, k=2))
                        ProductImage.objects.create(
                            product=product, image=image or DEFAULT_IMAGE, alt=title
                        )
                        Specification.objects.create(
                            product=product, name="Гарантия", value="12 месяцев"
                        )
                        Specification.objects.create(
                            product=product,
                            name="Цвет",
                            value=random.choice(["Чёрный", "Белый", "Серый"]),
                        )
                        for author in random.sample(
                            [c.full_name for c in customers], k=2
                        ):
                            Review.objects.create(
                                product=product,
                                author=author,
                                email="review@mail.ru",
                                text="Отличный товар, соответствует описанию.",
                                rate=random.randint(4, 5),
                            )
                    products.append(product)

        today = timezone.now().date()
        for product in random.sample(products, k=min(6, len(products))):
            Sale.objects.get_or_create(
                product=product,
                defaults={
                    "sale_price": (product.price * Decimal("0.8")).quantize(
                        Decimal("1")
                    ),
                    "date_from": today,
                    "date_to": today + timedelta(days=14),
                },
            )

        if not Order.objects.exists():
            for customer in customers:
                order = Order.objects.create(
                    user=customer,
                    full_name=customer.full_name,
                    email=customer.email,
                    phone=customer.phone or "",
                    delivery_type=Order.DELIVERY_ORDINARY,
                    payment_type=Order.PAYMENT_ONLINE,
                    city="Москва",
                    address="Красная площадь, 1",
                    status=Order.STATUS_ACCEPTED,
                )
                for product in random.sample(products, k=3):
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        count=random.randint(1, 3),
                        price=product.price,
                    )
                order.recalculate_total()
                order.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo data ready: {User.objects.count()} users, "
                f"{Category.objects.count()} categories, "
                f"{Product.objects.count()} products, "
                f"{Order.objects.count()} orders."
            )
        )
