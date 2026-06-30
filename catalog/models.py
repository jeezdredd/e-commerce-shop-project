from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from common.models import SoftDeleteModel


class Category(SoftDeleteModel):
    title = models.CharField(max_length=255)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subcategories",
    )
    image = models.ImageField(upload_to="categories/", null=True, blank=True)
    icon = models.FileField(upload_to="categories/icons/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    sort_index = models.PositiveIntegerField(default=0)
    is_favorite = models.BooleanField(default=False)

    class Meta:
        verbose_name = "category"
        verbose_name_plural = "categories"
        ordering = ["sort_index", "title"]

    def __str__(self):
        return self.title

    @property
    def image_src(self):
        return self.icon.url if self.icon else (self.image.url if self.image else "")


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Product(SoftDeleteModel):
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products"
    )
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    count = models.PositiveIntegerField(default=0)
    description = models.CharField(max_length=500, blank=True)
    full_description = models.TextField(blank=True)
    free_delivery = models.BooleanField(default=False)
    limited_edition = models.BooleanField(default=False)
    is_banner = models.BooleanField(default=False)
    sort_index = models.PositiveIntegerField(default=0)
    purchases_count = models.PositiveIntegerField(default=0)
    date = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="products")

    class Meta:
        ordering = ["sort_index", "-purchases_count"]

    def __str__(self):
        return self.title

    @property
    def average_rating(self):
        agg = self.reviews.aggregate(models.Avg("rate"))
        return round(agg["rate__avg"] or 0, 1)


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="products/")
    alt = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.alt or f"image {self.pk}"


class Specification(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="specifications"
    )
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}: {self.value}"


class Review(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    author = models.CharField(max_length=255)
    email = models.EmailField()
    text = models.TextField()
    rate = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.author} -> {self.product}"


class Sale(models.Model):
    product = models.OneToOneField(
        Product, on_delete=models.CASCADE, related_name="sale"
    )
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    date_from = models.DateField()
    date_to = models.DateField()

    def __str__(self):
        return f"sale {self.product}"
