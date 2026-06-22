from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


# =========================================================
# CUSTOM USER MODEL
# =========================================================
class User(AbstractUser):
    ROLE_CHOICES = (
        ('Admin', 'Admin'),
        ('Farmer', 'Farmer'),
        ('Consumer', 'Consumer'),
        ('Buyer', 'Buyer'),
        ('Cooperative', 'Cooperative'),
    )

    phone = models.CharField(max_length=20, unique=True)
    address = models.TextField(blank=True, null=True)
    role = models.CharField(
        max_length=15,
        choices=ROLE_CHOICES,
        default='Consumer'
    )

    email = models.EmailField(blank=True, null=True)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.phone


# =========================================================
# CATEGORY MODEL
# =========================================================
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


# =========================================================
# ITEM / PRODUCT MODEL
# =========================================================
class Item(models.Model):
    ORGANIC = 'Organic'
    INORGANIC = 'Inorganic'

    TYPE_CHOICES = [
        (ORGANIC, 'Organic'),
        (INORGANIC, 'Inorganic'),
    ]

    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='items'
    )

    image = models.ImageField(
        upload_to='item_images/',
        blank=True,
        null=True
    )

    name = models.CharField(max_length=255)

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='items'
    )

    item_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES
    )

    description = models.TextField()

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    stock = models.PositiveIntegerField(default=0)

    size = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    contact_note = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Contact info or note (e.g. cooperative phone number)'
    )

    added_date = models.DateTimeField(auto_now_add=True)

    updated_date = models.DateTimeField(auto_now=True)

    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ['-added_date']

    def __str__(self):
        return self.name


# =========================================================
# ORDER MODEL
# =========================================================
class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )

    ordered_date = models.DateTimeField(auto_now_add=True)

    billing_address = models.TextField()

    shipping_address = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return f"Order #{self.id}"

    @property
    def get_total_order_price(self):
        return sum(
            item.get_total_item_price
            for item in self.order_items.all()
        )


# =========================================================
# ORDER ITEM MODEL
# =========================================================
class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='order_items'
    )

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE
    )

    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('order', 'item')

    def __str__(self):
        return f"{self.quantity} × {self.item.name}"

    @property
    def get_total_item_price(self):
        return self.quantity * self.item.price


# =========================================================
# TRANSACTION MODEL
# =========================================================
class Transaction(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions'
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='transactions'
    )

    transaction_id = models.CharField(
        max_length=100,
        unique=True
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.transaction_id


# =========================================================
# REVIEW MODEL
# =========================================================
class Review(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    rating = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )

    feedback = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'item')

    def __str__(self):
        return f"{self.item.name} review"