from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Product, Category, Wishlist, Vendor, UserProfile, Order, ProductReview
from .forms import ProductSearchForm, UserRegistrationForm, LoginForm, UserProfileForm, OrderForm, ProductReviewForm
from django.views.generic import DetailView
from django.contrib.auth.decorators import login_required
from django.utils import timezone


# Homepage View
def homepage(request):
    """Display the homepage with categories and recent products"""
    categories = Category.objects.all()  # Retrieve all categories
    featured_vendors = Vendor.objects.all()[:5] 
    recent_products = Product.objects.order_by('-created_at')[:6]  # Latest 6 products
    context = {
        'featured_vendors': featured_vendors,
        'recent_products': recent_products,
    }
    return render(request, 'marketplace/homepage.html', context)

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.all()

    review_form = ProductReviewForm()
    order_form = OrderForm()
    
    if request.method == 'POST':
        if 'review' in request.POST:
            review_form = ProductReviewForm(request.POST)
            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.product = product
                review.user = request.user
                review.save()
                return redirect('product_detail', product_id=product.id)
        elif 'order' in request.POST:
            order_form = OrderForm(request.POST)
            if order_form.is_valid():
                order = order_form.save(commit=False)
                order.product = product
                order.user = request.user
                order.total_price = product.price * order_form.cleaned_data['quantity']
                order.save()
                return redirect('order_success')

    else:
        review_form = ProductReviewForm()
        order_form = OrderForm()

    return render(request, 'marketplace/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'review_form': review_form,
        'order_form': order_form,
    })

def products(request):
    form = ProductSearchForm(request.GET or None)
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category', '')

    products = Product.objects.all()

    if search_query:
        products = products.filter(name__icontains=search_query)

    if category_id:
        products = products.filter(category_id=category_id)

    categories = Category.objects.all()

    return render(request, 'marketplace/products.html', {
        'products': products,
        'categories': categories,
        'search_query': search_query,  # Pass search_query to the template
        'category_id': category_id,    # Pass category_id to the template
    })

class VendorDetailView(DetailView):
    model = Vendor
    template_name = 'marketplace/vendor_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = self.object.products.all()  # Get all products related to this vendor
        return context

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save()
                messages.success(request, 'Registration successful! You can now log in.')
                # Create UserProfile for every user
                profile_picture = form.cleaned_data.get('profile_picture')
                bio = form.cleaned_data.get('bio')
                user_profile, created = UserProfile.objects.get_or_create(user=user)

                if created:
                    user_profile.profile_picture = profile_picture
                    user_profile.bio = bio
                    user_profile.save()
                return redirect('login')  # Adjust this to your login URL name
            except IntegrityError:
                form.add_error(None, "A user profile already exists for this user.")
    else:
        form = UserRegistrationForm()

    return render(request, 'marketplace/register.html', {'form': form})

@login_required
def profile(request):
    return render(request, 'marketplace/profile.html', {'profile': request.user.profile})

def vendor_dashboard(request):
    if hasattr(request.user, 'vendor'):
        vendor = request.user.vendor
        products = vendor.products.all()
        return render(request, 'marketplace/vendor_dashboard.html', {'vendor': vendor, 'products': products})
    else:
        return redirect('home')  # Redirect if not a vendor

@login_required
def place_order(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.total_price = product.price * order.quantity
            order.save()
            return redirect('order_success')  # You can create a success page
    else:
        form = OrderForm(initial={'product': product})
    return render(request, 'marketplace/place_order.html', {'form': form, 'product': product})

@login_required
def user_orders(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'marketplace/user_orders.html', {'orders': orders})

@login_required
def submit_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.save()
            return redirect('product_detail', product_id=product.id)
    else:
        form = ProductReviewForm()
    return render(request, 'marketplace/submit_review.html', {'form': form, 'product': product})

def category_products(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = category.products.all()
    return render(request, 'marketplace/category_products.html', {'category': category, 'products': products})

def order_success(request):
    return render(request, 'marketplace/order_success.html')

def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.get_or_create(user=request.user, product=product)
    return redirect('product_detail', product_id=product.id)

def view_wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'marketplace/wishlist.html', {'wishlist_items': wishlist_items})

def some_view(request):
    return render(request, 'marketplace/homepage.html', {
        'current_year': timezone.now().year,
    })

def about(request):
    return render(request, 'marketplace/about.html')

def contact(request):
    return render(request, 'marketplace/contact.html')

def privacy_policy(request):
    return render(request, 'marketplace/privacy_policy.html')

def terms_of_service(request):
    return render(request, 'marketplace/terms_of_service.html')

def edit_profile(request):
    # Get the user's profile or create a new one if it doesn't exist
    profile = get_object_or_404(UserProfile, user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')  # Redirect to the profile view after saving
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'marketplace/edit_profile.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('homepage')

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, 'Login successful!')
                return redirect('homepage')  # Replace 'homepage' with the correct URL name
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()

    return render(request, 'marketplace/login.html', {'form': form})