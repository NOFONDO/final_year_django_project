from django import forms
from PIL import Image as PILImage
from PIL.ExifTags import TAGS
from datetime import datetime, timedelta

from .models import User, Category, Item, Order, Transaction, Review, ConversationMessage, Cart, CartItem


# =========================================================
# USER REGISTRATION FORM — with NIC upload
# =========================================================
class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ['username', 'phone', 'email', 'password', 'role', 'address', 'nic_document']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }
        help_texts = {
            'nic_document': (
                'Farmers and Cooperatives: Upload a photo of your National ID Card (NIC). '
                'Your account will be reviewed and approved before you can list products.'
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        nic = cleaned_data.get('nic_document')
        if role in ('Farmer', 'Cooperative') and not nic:
            raise forms.ValidationError(
                'Farmers and Cooperatives must upload a National ID Card (NIC) for verification.'
            )
        return cleaned_data


# =========================================================
# CATEGORY FORM
# =========================================================
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']


# =========================================================
# EXIF IMAGE VALIDATOR
# Used by ItemForm to reject old/fake product images
# =========================================================
def validate_image_recency(image):
    """
    Reads EXIF metadata from an uploaded image.
    Rejects images taken more than 7 days ago.
    This prevents farmers from uploading old/stolen product photos.
    """
    MAX_IMAGE_AGE_DAYS = 7

    try:
        img = PILImage.open(image)
        exif_data = img._getexif()

        if exif_data:
            # Map EXIF tag numbers to readable names
            exif = {
                TAGS.get(tag, tag): value
                for tag, value in exif_data.items()
            }

            # DateTimeOriginal = exact moment shutter was pressed
            # DateTime = file modification time (fallback)
            date_taken_str = exif.get('DateTimeOriginal') or exif.get('DateTime')

            if date_taken_str:
                date_taken = datetime.strptime(date_taken_str, '%Y:%m:%d %H:%M:%S')
                age = datetime.now() - date_taken

                if age > timedelta(days=MAX_IMAGE_AGE_DAYS):
                    raise forms.ValidationError(
                        f'This photo was taken on {date_taken.strftime("%B %d, %Y")} '
                        f'which is more than {MAX_IMAGE_AGE_DAYS} days ago. '
                        f'Please upload a recent photo of your product taken within '
                        f'the last {MAX_IMAGE_AGE_DAYS} days to verify it is genuine.'
                    )
            else:
                # No date found in EXIF — image may be a screenshot or
                # downloaded from internet (EXIF was stripped).
                # We raise a warning-level error here.
                raise forms.ValidationError(
                    'We could not verify when this photo was taken. '
                    'Please upload an original photo taken directly from your camera '
                    'or smartphone. Screenshots and downloaded images are not accepted.'
                )

        else:
            # No EXIF data at all — very likely a screenshot or web image
            raise forms.ValidationError(
                'This image has no camera metadata (EXIF). '
                'Please take a fresh photo of your product using your phone camera '
                'and upload it directly. Screenshots are not accepted.'
            )

    except forms.ValidationError:
        # Re-raise our own validation errors
        raise

    except Exception:
        # If PIL crashes reading EXIF for any other reason, allow the image
        # (better to allow than to block legitimate uploads due to a bug)
        pass

    # Reset file pointer so Django can still save the image after reading it
    image.seek(0)
    return image


# =========================================================
# ITEM FORM — for verified farmers to list products
# =========================================================
class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            'name', 'image', 'category', 'item_type',
            'description', 'price', 'stock', 'size', 'contact_note'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        help_texts = {
            'image': (
                'Take a fresh photo of your product today and upload it. '
                'Photos older than 7 days will be rejected for authenticity reasons.'
            ),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            validate_image_recency(image)
        return image


# =========================================================
# ORDER FORM
# =========================================================
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'billing_address', 'shipping_address',
            'payment_method', 'mobile_money_number', 'total'
        ]
        widgets = {
            'billing_address': forms.Textarea(attrs={'rows': 3}),
            'shipping_address': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        momo_number = cleaned_data.get('mobile_money_number')
        if payment_method in ('MTN_MOMO', 'ORANGE_MONEY') and not momo_number:
            raise forms.ValidationError(
                'Please enter your Mobile Money number for this payment method.'
            )
        return cleaned_data


# =========================================================
# TRANSACTION FORM
# =========================================================
class TransactionForm(forms.ModelForm):
    transaction_id = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Unique Transaction ID'})
    )

    class Meta:
        model = Transaction
        fields = ['transaction_id', 'amount']

# =========================================================
# REVIEW FORM
# =========================================================
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'feedback']
        widgets = {
            'feedback': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating < 1 or rating > 5:
            raise forms.ValidationError('Rating must be between 1 and 5.')
        return rating


# =========================================================
# MESSAGE FORM
# =========================================================
class MessageForm(forms.ModelForm):
    class Meta:
        model = ConversationMessage
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Type your message here...'
            }),
        }
        labels = {
            'content': ''
        }