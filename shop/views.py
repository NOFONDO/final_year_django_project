import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from .models import (
    Category, Item, Order, OrderItem, Review, Transaction,
    Cart, CartItem, Conversation, ConversationMessage, User
)
from .forms import (
    UserForm, ItemForm, CategoryForm, OrderForm,
    ReviewForm, TransactionForm, MessageForm
)


# ============================================================
# HELPERS
# ============================================================
def get_categories():
    return Category.objects.all()


def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


# ============================================================
# HOME
# ============================================================
def home(request):
    categories = get_categories()
    items = Item.objects.filter(
        is_available=True,
        farmer__verification_status='Approved'
    )[:6]
    return render(request, 'home.html', {'categories': categories, 'items': items})


# ============================================================
# CATEGORY PAGE
# ============================================================
def category_page(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    items = Item.objects.filter(
        category=category,
        is_available=True,
        farmer__verification_status='Approved'
    )
    categories = get_categories()
    return render(request, 'category_page.html', {
        'category': category,
        'items': items,
        'categories': categories
    })


# ============================================================
# PRODUCT DETAIL
# ============================================================
def product_detail(request, item_id):
    categories = get_categories()
    item = get_object_or_404(Item, id=item_id)
    reviews = Review.objects.filter(item=item)
    related_items = Item.objects.filter(
        category=item.category
    ).exclude(id=item_id)[:3]
    return render(request, 'product_detail.html', {
        'categories': categories,
        'item': item,
        'reviews': reviews,
        'related_items': related_items
    })


# ============================================================
# CART (Cart model based)
# ============================================================
@login_required
def cart(request):
    categories = get_categories()
    user_cart = get_or_create_cart(request.user)
    return render(request, 'cart.html', {
        'categories': categories,
        'cart': user_cart
    })


@login_required
def add_to_cart(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    user_cart = get_or_create_cart(request.user)

    if item.stock > 0:
        cart_item, created = CartItem.objects.get_or_create(
            cart=user_cart, item=item
        )
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        item.stock -= 1
        item.save()
        messages.success(request, f'"{item.name}" added to cart.')
    else:
        messages.warning(request, f'"{item.name}" is out of stock.')
    return redirect('cart')


@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    user_cart = get_or_create_cart(request.user)
    cart_item = get_object_or_404(CartItem, cart=user_cart, item=item)

    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
        item.stock += 1
        item.save()
    else:
        item.stock += cart_item.quantity
        item.save()
        cart_item.delete()

    messages.success(request, f'"{item.name}" removed from cart.')
    return redirect('cart')


# ============================================================
# CHECKOUT
# ============================================================
@login_required
def checkout(request):
    categories = get_categories()
    user_cart = get_or_create_cart(request.user)

    if user_cart.cart_items.count() == 0:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart')

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.total = user_cart.get_total_price
            order.save()

            # Move cart items to order items
            for cart_item in user_cart.cart_items.all():
                OrderItem.objects.create(
                    order=order,
                    item=cart_item.item,
                    quantity=cart_item.quantity
                )

            # Clear cart
            user_cart.cart_items.all().delete()

            return redirect('process_payment', order_id=order.id)
    else:
        form = OrderForm()

    return render(request, 'checkout.html', {
        'categories': categories,
        'form': form,
        'cart': user_cart
    })


# ============================================================
# PAYMENT
# ============================================================
@login_required
def process_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    transaction_id = str(uuid.uuid4())
    Transaction.objects.create(
        user=request.user,
        order=order,
        transaction_id=transaction_id,
        amount=order.get_total_order_price
    )

    order.status = 'Completed'
    order.save()

    return redirect('payment_success', transaction_id=transaction_id)


@login_required
def payment_success(request, transaction_id):
    transaction = get_object_or_404(Transaction, transaction_id=transaction_id)
    return render(request, 'payment_success.html', {'transaction': transaction})


# ============================================================
# PROFILE
# ============================================================
@login_required
def profile(request):
    categories = get_categories()
    user = request.user
    orders = user.orders.all().order_by('-ordered_date')
    return render(request, 'profile.html', {
        'categories': categories,
        'user': user,
        'orders': orders
    })


# ============================================================
# ADD ITEM (farmer must be verified)
# ============================================================
@login_required
def add_item(request):
    categories = get_categories()

    if request.user.role not in ('Farmer', 'Cooperative'):
        messages.error(request, 'Only farmers and cooperatives can list products.')
        return redirect('home')

    # --- DEFENSE ANSWER: Block unverified farmers ---
    if not request.user.is_verified:
        messages.warning(
            request,
            'Your account is pending verification. '
            'An admin will review your NIC and approve your account before you can list products.'
        )
        return redirect('verification_pending')

    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.farmer = request.user
            item.save()
            messages.success(request, f'"{item.name}" listed successfully!')
            return redirect('home')
    else:
        form = ItemForm()
    return render(request, 'add_item.html', {'categories': categories, 'form': form})


# ============================================================
# VERIFICATION PENDING PAGE
# ============================================================
@login_required
def verification_pending(request):
    categories = get_categories()
    return render(request, 'verification_pending.html', {
        'categories': categories,
        'user': request.user
    })


# ============================================================
# REGISTER
# ============================================================
def register(request):
    categories = get_categories()
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            # Buyers/Consumers are auto-approved; Farmers need admin review
            if form.cleaned_data['role'] in ('Farmer', 'Cooperative'):
                user.verification_status = 'Pending'
            else:
                user.verification_status = 'Approved'
            user.save()
            login(request, user)
            if user.role in ('Farmer', 'Cooperative'):
                messages.info(
                    request,
                    'Registration successful! Your NIC is under review. '
                    'You will be able to list products after admin approval.'
                )
                return redirect('verification_pending')
            messages.success(request, 'Welcome! Your account is ready.')
            return redirect('home')
    else:
        form = UserForm()
    return render(request, 'register.html', {'categories': categories, 'form': form})


# ============================================================
# LOGIN / LOGOUT
# ============================================================
def login_view(request):
    categories = get_categories()
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html', {'categories': categories})


@login_required
def logout_view(request):
    logout(request)
    return redirect('home')


# ============================================================
# REVIEWS
# ============================================================
@login_required
def add_review(request, item_id):
    categories = get_categories()
    item = get_object_or_404(Item, id=item_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.item = item
            review.save()
            messages.success(request, 'Review submitted!')
            return redirect('product_detail', item_id=item_id)
    else:
        form = ReviewForm()
    return render(request, 'add_review.html', {
        'categories': categories,
        'form': form,
        'item': item
    })


# ============================================================
# SEARCH
# ============================================================
def search(request):
    categories = get_categories()
    query = request.GET.get('q', '')
    results = []
    if query:
        results = Item.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            farmer__verification_status='Approved',
            is_available=True
        )
    return render(request, 'search_results.html', {
        'categories': categories,
        'query': query,
        'results': results
    })


# ============================================================
# MESSAGING VIEWS (NEW)
# ============================================================
@login_required
def inbox(request):
    """Show all conversations for the current user"""
    categories = get_categories()
    conversations = request.user.conversations.all().order_by('-updated_at')
    return render(request, 'messaging/inbox.html', {
        'categories': categories,
        'conversations': conversations
    })


@login_required
def conversation_detail(request, conversation_id):
    """View and reply to a conversation"""
    categories = get_categories()
    conversation = get_object_or_404(
        Conversation, id=conversation_id
    )

    # Security: only participants can view
    if request.user not in conversation.participants.all():
        messages.error(request, 'You do not have access to this conversation.')
        return redirect('inbox')

    # Mark messages as read
    conversation.conversation_messages.filter(
        is_read=False
    ).exclude(sender=request.user).update(is_read=True)

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.conversation = conversation
            msg.sender = request.user
            msg.save()
            conversation.updated_at = timezone.now()
            conversation.save()
            return redirect('conversation_detail', conversation_id=conversation.id)
    else:
        form = MessageForm()

    all_messages = conversation.conversation_messages.all()
    return render(request, 'messaging/conversation.html', {
        'categories': categories,
        'conversation': conversation,
        'all_messages': all_messages,
        'form': form
    })


@login_required
def start_conversation(request, farmer_id, item_id=None):
    """Start or resume a conversation with a farmer about a product"""
    categories = get_categories()
    farmer = get_object_or_404(User, id=farmer_id)
    item = get_object_or_404(Item, id=item_id) if item_id else None

    if farmer == request.user:
        messages.error(request, 'You cannot message yourself.')
        return redirect('home')

    # Find existing conversation between these two users about this item
    existing = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=farmer
    )
    if item:
        existing = existing.filter(item=item)

    if existing.exists():
        conversation = existing.first()
    else:
        conversation = Conversation.objects.create(item=item)
        conversation.participants.add(request.user, farmer)
        conversation.save()

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.conversation = conversation
            msg.sender = request.user
            msg.save()
            return redirect('conversation_detail', conversation_id=conversation.id)
    else:
        form = MessageForm()

    return render(request, 'messaging/start_conversation.html', {
        'categories': categories,
        'farmer': farmer,
        'item': item,
        'form': form,
        'conversation': conversation
    })

# ============================================================
# ABOUT US
# ============================================================
def about_us(request):
    return render(request, 'about_us.html')


# ============================================================
# DASHBOARD (for farmers to see their listings)
# ============================================================
@login_required
def farmer_dashboard(request):
    categories = get_categories()
    if request.user.role not in ('Farmer', 'Cooperative'):
        return redirect('home')
    my_items = Item.objects.filter(farmer=request.user)
    return render(request, 'farmer_dashboard.html', {
        'categories': categories,
        'my_items': my_items,
        'user': request.user
    })
