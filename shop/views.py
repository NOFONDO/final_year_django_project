from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Category, Item, Order, Review, Transaction
from .forms import UserForm, ItemForm, CategoryForm, OrderForm, ReviewForm, TransactionForm
from django.contrib.auth import authenticate, login
from django.db.models import Q
from django.contrib.auth import login
from django.shortcuts import redirect, render
from .models import Category  # Ensure you have the correct import for Category


# Home Page
def home(request):
    categories = Category.objects.all()
    items = Item.objects.all()[:6] # Display 6 sample products
    return render(request, 'home.html', {'categories': categories, 'items': items})


# Category Page
from django.shortcuts import render, get_object_or_404
from .models import Category, Item

def category_page(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    items = Item.objects.filter(category=category)
    categories = Category.objects.all()  # Fetch all categories
    return render(request, 'category_page.html', {
        'category': category,
        'items': items,
        'categories': categories  # Pass all categories to the template
    })


# Product Detail Page
def product_detail(request, item_id):
    categories = Category.objects.all()
    item = get_object_or_404(Item, id=item_id)
    reviews = Review.objects.filter(item=item)
    related_items = Item.objects.filter(category=item.category).exclude(id=item_id)[:3]  # Display related products
    return render(request, 'product_detail.html', {'categories': categories,'item': item, 'reviews': reviews, 'related_items': related_items})

# Cart Page
@login_required
def cart(request):
    categories = Category.objects.all()
    order, created = Order.objects.get_or_create(user=request.user, status='Pending')
    return render(request, 'cart.html', {'categories': categories,'order': order})

# Checkout Page
@login_required
def checkout(request):
    order = request.user.orders.filter(status='Pending').first()
    #order = request.user.order_set.filter(status='Pending').first()


    if not order:
        return redirect('cart')  # Redirect to cart if no pending order is found

    # Update the total in the order before displaying the checkout page
    order.total = order.get_total_order_price
    order.save()
    categories = Category.objects.all()

    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            order = form.save(commit=False)
            order.status = 'Ordered'
            order.total = order.get_total_order_price  # Recalculate the total
            order.save()
            print(f"Redirecting to payment page for Order ID: {order.id}")
            return redirect('payment_page')  # Placeholder for payment gateway
        else:
            print(form.errors)  # Print form errors for debugging
    else:
        form = OrderForm(instance=order)

    return render(request, 'checkout.html', {'categories': categories, 'form': form, 'order': order})



# Profile Page
from django.shortcuts import render

def profile(request):
    categories = Category.objects.all()
    user = request.user
    orders = user.orders.all().order_by('-ordered_date')  # Order by newest first
    return render(request, 'profile.html', {'categories': categories,'user': user, 'orders': orders})


# Add Item Page (For Farmers)
@login_required
def add_item(request):
    categories = Category.objects.all()
    if request.user.role in ('Farmer', 'Cooperative'):
        if request.method == 'POST':
            form = ItemForm(request.POST, request.FILES)
            if form.is_valid():
                item = form.save(commit=False)
                item.farmer = request.user
                item.save()
                return redirect('home')  # Redirect after successful addition
        else:
            form = ItemForm()
        return render(request, 'add_item.html', {'categories': categories,'form': form})
    else:
        return redirect('home')


def register(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.role = form.cleaned_data['role']  # Set the user role
            user.address = form.cleaned_data['address']  # Set the user address
            user.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserForm()
    return render(request, 'register.html', {'categories': categories, 'form': form})


# Login Page
def login_view(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
    return render(request, 'login.html',{'categories': categories})

# Product Review Page
@login_required
def add_review(request, item_id):
    categories = Category.objects.all()
    item = get_object_or_404(Item, id=item_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.item = item
            review.save()
            return redirect('product_detail', item_id=item_id)  # Redirect after review submission
    else:
        form = ReviewForm()
    return render(request, 'add_review.html', {'categories': categories,'form': form, 'item': item})

from django.contrib.auth import logout

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

# Search View
def search(request):
    categories = Category.objects.all()
    query = request.GET.get('q')
    results = []
    
    if query:
        results = Item.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    
    return render(request, 'search_results.html', {'categories': categories,'query': query, 'results': results})


from django.shortcuts import redirect, get_object_or_404
from .models import Item, Order

from django.shortcuts import redirect, get_object_or_404
from .models import Item, Order, OrderItem

@login_required
def add_to_cart(request, item_id):
    
    item = get_object_or_404(Item, id=item_id)
    order, created = Order.objects.get_or_create(user=request.user, status='Pending')
    
    # Check if the item is already in the cart
    order_item, created = OrderItem.objects.get_or_create(order=order, item=item)
    
    if item.stock > 0:
        order_item.quantity += 1  # Increase quantity if already in cart
        order_item.save()
        item.stock -= 1  # Decrease stock
        item.save()

    return redirect('cart')


@login_required
def remove_from_cart(request, item_id):
    order = Order.objects.get(user=request.user, status='Pending')
    item = get_object_or_404(Item, id=item_id)
    order_item = get_object_or_404(OrderItem, order=order, item=item)
    
    if order_item.quantity > 1:
        order_item.quantity -= 1  # Decrease quantity if more than 1
        order_item.save()
        item.stock += 1  # Increase stock
        item.save()
    else:
        order_item.delete()  # Remove item if quantity is 1

    return redirect('cart')

import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Transaction, Order

# Payment page view
@login_required
def payment_page(request):
    order = request.user.orders.filter(status='Pending').first()

    if not order:
        return redirect('cart')

    if request.method == 'POST':
        billing_address = request.POST.get('billing_address')
        shipping_address = request.POST.get('shipping_address')

        # Update the order with billing and shipping addresses
        order.billing_address = billing_address
        order.shipping_address = shipping_address
        order.save()

        # Process payment
        return redirect('process_payment')

    return render(request, 'payment_page.html', {'order': order})



# Process payment (static)
@login_required
def process_payment(request):
    # Get the user's pending order
    order = request.user.orders.filter(status='Pending').first()

    # If no pending order, redirect to the cart
    if not order:
        return redirect('cart')

    # Simulate a transaction by generating a unique transaction ID
    transaction_id = str(uuid.uuid4())
    amount = order.get_total_order_price  # Ensure this property is defined correctly in the Order model

    # Create a new transaction entry
    transaction = Transaction.objects.create(
        user=request.user,
        order=order,
        transaction_id=transaction_id,
        amount=amount
    )

    # Update the order status to 'Ordered'
    order.status = 'Ordered'
    order.save()

    # Redirect to a success page
    return redirect('payment_success', transaction_id=transaction_id)

# Payment success page view
@login_required
def payment_success(request, transaction_id):
    # Get the transaction details
    order = request.user.orders.filter(status='Ordered').last()
    order.status = 'Completed'
    order.save()
    transaction = get_object_or_404(Transaction, transaction_id=transaction_id)
    return render(request, 'payment_success.html', {'transaction': transaction})

def about_us(request):
    return render(request, 'about_us.html')
