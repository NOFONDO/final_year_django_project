from django.urls import path
from .views import home, category_page, product_detail, cart, checkout, profile, add_item, register, login_view, add_review, logout_view, search,add_to_cart,remove_from_cart,payment_page,process_payment,payment_success, about_us

urlpatterns = [
    path('', home, name='home'),
    path('category/<int:category_id>/', category_page, name='category_page'),  # Updated line
    path('product/<int:item_id>/', product_detail, name='product_detail'),
    path('cart/', cart, name='cart'),
    path('checkout/', checkout, name='checkout'),
    path('profile/', profile, name='profile'),
    path('add_item/', add_item, name='add_item'),
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('add_review/<int:item_id>/', add_review, name='add_review'),
    path('logout/', logout_view, name='logout'),
    path('search/', search, name='search'),
    path('add_to_cart/<int:item_id>/', add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('payment/', payment_page, name='payment_page'),
    path('process-payment/', process_payment, name='process_payment'),
    path('payment-success/<str:transaction_id>/', payment_success, name='payment_success'),
    path('about-us/', about_us, name='about_us'),
]
