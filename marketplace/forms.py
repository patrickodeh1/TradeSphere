from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Product, ProductReview, Category


class UserRegistrationForm(UserCreationForm):
    """Form for user registration"""
    USER_TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
    ]
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email'})
    )
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-input'})
    )
    bio = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Tell us about yourself'}),
        required=False
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'user_type', 'profile_picture', 'bio']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Username'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Confirm Password'})


class LoginForm(forms.Form):
    """Form for user login"""
    username = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Password'})
    )


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile"""
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email'})
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'profile_picture', 'bio', 'phone',
            'shipping_address', 'shipping_city', 'shipping_state',
            'shipping_postal_code', 'shipping_country'
        ]
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-input'}),
            'bio': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Bio'}),
            'phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Phone Number'}),
            'shipping_address': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Street Address'}),
            'shipping_city': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'City'}),
            'shipping_state': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'State'}),
            'shipping_postal_code': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Postal Code'}),
            'shipping_country': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Country'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            # Update user fields
            user = profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save()
            profile.save()
        return profile


class CheckoutForm(forms.Form):
    """Form for checkout"""
    full_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Full Name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email'})
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Phone Number'})
    )
    shipping_address = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Street Address'})
    )
    shipping_city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'City'})
    )
    shipping_state = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'State'})
    )
    shipping_postal_code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Postal Code'})
    )
    shipping_country = forms.CharField(
        max_length=100,
        initial='Nigeria',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Country'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Order notes (optional)'})
    )


class ProductUploadForm(forms.ModelForm):
    """Form for vendors to upload products"""
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'compare_at_price', 'image', 'category', 'stock', 'is_featured']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Product Name'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Product Description'}),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Price', 'step': '0.01'}),
            'compare_at_price': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Compare at Price (optional)', 'step': '0.01'}),
            'image': forms.FileInput(attrs={'class': 'form-input'}),
            'category': forms.Select(attrs={'class': 'form-input'}),
            'stock': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Stock Quantity'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class ProductSearchForm(forms.Form):
    """Form for product search"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'search-input', 'placeholder': 'Search products...'})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class ProductReviewForm(forms.ModelForm):
    """Form for product reviews"""
    class Meta:
        model = ProductReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(
                choices=[(i, f'{i} Stars') for i in range(1, 6)],
                attrs={'class': 'form-input'}
            ),
            'comment': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Write your review...'})
        }