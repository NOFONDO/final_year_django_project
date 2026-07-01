from django.urls import path
from . import views

urlpatterns = [
    # ---- Core pages ----
    path('', views.home, name='home'),
    path('category/<int:category_id>/', views.category_page, name='category_page'),
    path('product/<int:item_id>/', views.product_detail, name='product_detail'),
    path('about-us/', views.about_us, name='about_us'),
    path('search/', views.search, name='search'),

    # ---- Auth ----
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),

    # ---- Verification ----
    path('verification-pending/', views.verification_pending, name='verification_pending'),

    # ---- Farmer tools ----
    path('add-item/', views.add_item, name='add_item'),
    path('dashboard/', views.farmer_dashboard, name='farmer_dashboard'),

    # ---- Reviews ----
    path('add-review/<int:item_id>/', views.add_review, name='add_review'),

    # ---- Cart ----
    path('cart/', views.cart, name='cart'),
    path('add-to-cart/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),

    # ---- Checkout & Payment ----
    path('checkout/', views.checkout, name='checkout'),
    path('process-payment/<int:order_id>/', views.process_payment, name='process_payment'),
    path('payment-success/<str:transaction_id>/', views.payment_success, name='payment_success'),

    # ---- Messaging ----
    path('inbox/', views.inbox, name='inbox'),
    path('messages/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('contact/<int:farmer_id>/', views.start_conversation, name='start_conversation'),
    path('contact/<int:farmer_id>/item/<int:item_id>/', views.start_conversation, name='start_conversation_item'),
]
