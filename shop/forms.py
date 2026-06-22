from django import forms
from .models import User, Category, Item, Order, Transaction, Review

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    
    class Meta:
        model = User
        fields = ['username', 'phone', 'email', 'password', 'role', 'address']

# Category form
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

# Item form for farmers to add products
class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'image', 'category', 'item_type', 'description', 'price', 'stock', 'size', 'contact_note']

# Order form for creating or updating orders
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['billing_address', 'shipping_address', 'total']

# Transaction form
class TransactionForm(forms.ModelForm):
    transaction_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Unique Transaction ID'}))

    class Meta:
        model = Transaction
        fields = ['transaction_id', 'amount']

# Review form for submitting reviews
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'feedback']

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating < 1 or rating > 5:
            raise forms.ValidationError('Rating must be between 1 and 5.')
        return rating
