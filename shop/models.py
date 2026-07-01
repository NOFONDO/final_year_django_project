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

    VERIFICATION_STATUS = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )

    phone = models.CharField(max_length=20, unique=True)
    address = models.TextField(blank=True, null=True)
    role = models.CharField(
        max_length=15,
        choices=ROLE_CHOICES,
        default='Consumer'
    )
    email = models.EmailField(blank=True, null=True)

    # --- VERIFICATION FIELDS (answers defense question) ---
    nic_document = models.FileField(
        upload_to='nic_documents/',
        blank=True,
        null=True,
        help_text='Upload National ID Card (NIC) photo for verification'
    )
    verification_status = models.CharField(
        max_length=10,
        choices=VERIFICATION_STATUS,
        default='Pending'
    )
    rejection_reason = models.TextField(
        blank=True,
        null=True,
        help_text='Reason if verification is rejected'
    )
    verified_at = models.DateTimeField(blank=True, null=True)
    verified_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_users'
    )

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.username} ({self.phone})"

    @property
    def is_verified(self):
        return self.verification_status == 'Approved'

    @property
    def needs_verification(self):
        """Farmers and Cooperatives must be verified before listing products"""
        return self.role in ('Farmer', 'Cooperative')


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
# CART MODEL (replaces session-based cart)
# =========================================================
class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"

    @property
    def get_total_price(self):
        return sum(item.get_total_price for item in self.cart_items.all())

    @property
    def total_items(self):
        return sum(item.quantity for item in self.cart_items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'item')

    def __str__(self):
        return f"{self.quantity} × {self.item.name}"

    @property
    def get_total_price(self):
        return self.quantity * self.item.price


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

    PAYMENT_METHOD_CHOICES = (
        ('MTN_MOMO', 'MTN Mobile Money'),
        ('ORANGE_MONEY', 'Orange Money'),
        ('CASH', 'Cash on Delivery'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )

    ordered_date = models.DateTimeField(auto_now_add=True)
    billing_address = models.TextField(default='')
    shipping_address = models.TextField(default='')

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='MTN_MOMO'
    )

    mobile_money_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='MTN/Orange Money number used for payment'
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"

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

    transaction_id = models.CharField(max_length=100, unique=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)

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
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    feedback = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'item')

    def __str__(self):
        return f"{self.item.name} review by {self.user.username}"


# =========================================================
# MESSAGE MODEL (NEW - Buyer <-> Farmer messaging)
# =========================================================
class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages',
        help_text='Item this message is about (optional)'
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"From {self.sender.username} to {self.receiver.username}"


# =========================================================
# CONVERSATION MODEL (groups messages between 2 users)
# =========================================================
class Conversation(models.Model):
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations'
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        names = ", ".join([u.username for u in self.participants.all()])
        return f"Conversation: {names}"

    @property
    def last_message(self):
        return self.conversation_messages.last()

    def unread_count(self, user):
        return self.conversation_messages.filter(is_read=False).exclude(sender=user).count()


class ConversationMessage(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='conversation_messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"[{self.conversation.id}] {self.sender.username}: {self.content[:40]}"
