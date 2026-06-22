from django.contrib import admin
from .models import Review,Transaction,Order,Item,Category,User,OrderItem
# Register your models here.

admin.site.register(Review)
admin.site.register(Transaction)
admin.site.register(Order)
admin.site.register(Item)
admin.site.register(Category)
admin.site.register(User)
admin.site.register(OrderItem)