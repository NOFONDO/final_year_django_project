from django.contrib import admin
from django.utils import timezone
from django.contrib import messages
from .models import (
    Review, Transaction, Order, Item, Category,
    User, OrderItem, Message, Conversation, ConversationMessage,
    Cart, CartItem
)


# =========================================================
# CUSTOM USER ADMIN — with NIC verification workflow
# =========================================================
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        'username', 'phone', 'role', 'verification_status',
        'nic_document', 'date_joined'
    ]
    list_filter = ['role', 'verification_status']
    search_fields = ['username', 'phone', 'email']
    readonly_fields = ['date_joined', 'verified_at', 'verified_by']

    actions = ['approve_users', 'reject_users']

    fieldsets = (
        ('Personal Info', {
            'fields': ('username', 'phone', 'email', 'address', 'role')
        }),
        ('Verification', {
            'fields': (
                'nic_document', 'verification_status',
                'rejection_reason', 'verified_at', 'verified_by'
            ),
            'description': (
                'Farmers and Cooperatives must upload their National ID Card (NIC). '
                'Use the actions below to Approve or Reject.'
            )
        }),
        ('Account Info', {
            'fields': ('is_active', 'is_staff', 'date_joined'),
            'classes': ('collapse',)
        }),
    )

    def approve_users(self, request, queryset):
        count = 0
        for user in queryset.filter(role__in=['Farmer', 'Cooperative']):
            if user.nic_document:
                user.verification_status = 'Approved'
                user.verified_at = timezone.now()
                user.verified_by = request.user
                user.save()
                count += 1
            else:
                self.message_user(
                    request,
                    f"{user.username} has no NIC document uploaded — cannot approve.",
                    level=messages.WARNING
                )
        self.message_user(request, f"✅ {count} user(s) approved successfully.")
    approve_users.short_description = "✅ Approve selected farmers/cooperatives"

    def reject_users(self, request, queryset):
        queryset.filter(role__in=['Farmer', 'Cooperative']).update(
            verification_status='Rejected',
            rejection_reason='Rejected by admin — please resubmit with valid NIC.'
        )
        self.message_user(request, "❌ Selected users have been rejected.")
    reject_users.short_description = "❌ Reject selected farmers/cooperatives"


# =========================================================
# ITEM ADMIN — shows farmer verification status
# =========================================================
@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'farmer', 'farmer_verified', 'category',
        'price', 'stock', 'is_available', 'added_date'
    ]
    list_filter = ['category', 'item_type', 'is_available']
    search_fields = ['name', 'farmer__username', 'farmer__phone']

    def farmer_verified(self, obj):
        if obj.farmer.is_verified:
            return "✅ Verified"
        return "⚠️ Unverified"
    farmer_verified.short_description = "Farmer Status"


# =========================================================
# ORDER ADMIN
# =========================================================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['get_total_item_price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'payment_method', 'total', 'ordered_date']
    list_filter = ['status', 'payment_method']
    search_fields = ['user__username', 'user__phone']
    inlines = [OrderItemInline]


# =========================================================
# MESSAGING ADMIN
# =========================================================
class ConversationMessageInline(admin.TabularInline):
    model = ConversationMessage
    extra = 0
    readonly_fields = ['sender', 'content', 'timestamp', 'is_read']

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_participants', 'item', 'updated_at']
    inlines = [ConversationMessageInline]

    def get_participants(self, obj):
        return " & ".join([u.username for u in obj.participants.all()])
    get_participants.short_description = "Between"


# =========================================================
# STANDARD REGISTRATIONS
# =========================================================
admin.site.register(Category)
admin.site.register(Review)
admin.site.register(Transaction)
admin.site.register(Cart)
admin.site.register(CartItem)

# Admin site branding
admin.site.site_header = "FarmLink Cameroon — Admin Portal"
admin.site.site_title = "FarmLink Cameroon"
admin.site.index_title = "Marketplace Management"
