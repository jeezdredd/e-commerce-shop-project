from rest_framework import serializers

from catalog.models import Category, Product, Review, Sale, Tag
from orders.models import Order, OrderItem


class ImageField(serializers.Serializer):
    src = serializers.CharField()
    alt = serializers.CharField()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class SubcategorySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "title", "image"]

    def get_image(self, obj):
        return {"src": obj.image_src, "alt": obj.title}


class CategorySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "title", "image", "subcategories"]

    def get_image(self, obj):
        return {"src": obj.image_src, "alt": obj.title}

    def get_subcategories(self, obj):
        qs = obj.subcategories.filter(is_active=True)
        return SubcategorySerializer(qs, many=True).data


def product_images(obj):
    return [
        {"src": img.image.url, "alt": img.alt or obj.title}
        for img in obj.images.all()
    ]


class ReviewSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)

    class Meta:
        model = Review
        fields = ["author", "email", "text", "rate", "date"]


class ProductShortSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    tags = TagSerializer(many=True)
    reviews = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "price",
            "count",
            "date",
            "title",
            "description",
            "free_delivery",
            "images",
            "tags",
            "reviews",
            "rating",
        ]

    def get_images(self, obj):
        return product_images(obj)

    def get_reviews(self, obj):
        return obj.reviews.count()

    def get_rating(self, obj):
        return obj.average_rating


class SpecificationSerializer(serializers.Serializer):
    name = serializers.CharField()
    value = serializers.CharField()


class ProductFullSerializer(ProductShortSerializer):
    full_description = serializers.CharField()
    specifications = SpecificationSerializer(many=True)
    reviews = ReviewSerializer(many=True)

    class Meta(ProductShortSerializer.Meta):
        fields = ProductShortSerializer.Meta.fields + [
            "full_description",
            "specifications",
        ]


class SaleSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="product.id")
    title = serializers.CharField(source="product.title")
    price = serializers.DecimalField(
        source="product.price", max_digits=10, decimal_places=2
    )
    images = serializers.SerializerMethodField()
    date_from = serializers.DateField(format="%m-%d")
    date_to = serializers.DateField(format="%m-%d")

    class Meta:
        model = Sale
        fields = ["id", "price", "sale_price", "date_from", "date_to", "title", "images"]

    def get_images(self, obj):
        return product_images(obj.product)


class OrderItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="product.id")
    category = serializers.IntegerField(source="product.category_id")
    title = serializers.CharField(source="product.title")
    description = serializers.CharField(source="product.description")
    free_delivery = serializers.BooleanField(source="product.free_delivery")
    images = serializers.SerializerMethodField()
    tags = TagSerializer(source="product.tags", many=True)
    reviews = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "category",
            "price",
            "count",
            "title",
            "description",
            "free_delivery",
            "images",
            "tags",
            "reviews",
            "rating",
        ]

    def get_images(self, obj):
        return product_images(obj.product)

    def get_reviews(self, obj):
        return obj.product.reviews.count()

    def get_rating(self, obj):
        return obj.product.average_rating


class OrderSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)
    products = OrderItemSerializer(source="items", many=True, read_only=True)
    payment_error = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "created_at",
            "full_name",
            "email",
            "phone",
            "delivery_type",
            "payment_type",
            "total_cost",
            "status",
            "city",
            "address",
            "products",
            "payment_error",
        ]

    def get_payment_error(self, obj):
        last = obj.payments.first()
        return last.error_text if last else ""
