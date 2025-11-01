from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from decouple import config
import requests
import json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import (Product, Category, Wishlist, Vendor, UserProfile, 
                     Order, OrderItem, ProductReview, Cart, CartItem)
from .forms import (ProductSearchForm, ProductUploadForm, UserRegistrationForm, 
                   LoginForm, UserProfileForm, ProductReviewForm, CheckoutForm)


def homepage(request):
    """Display the homepage with categories and featured products"""
    categories = Category.objects.all()[:6]
    featured_products = Product.objects.filter(is_featured=True, is_active=True)[:8]
    recent_products = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
    
    context = {
        'categories': categories,
        'featured_products': featured_products,
        'recent_products': recent_products,
        'current_year': timezone.now().year,
    }
    return render(request, 'marketplace/homepage.html', context)


def product_detail(request, product_id):
    """Display product details with reviews"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    reviews = product.reviews.all().order_by('-created_at')
    related_products = Product.objects.filter(
        category=product.category, 
        is_active=True
    ).exclude(id=product.id)[:4]
    
    # Check if product is in wishlist
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
    
    context = {
        'product': product,
        'reviews': reviews,
        'related_products': related_products,
        'in_wishlist': in_wishlist,
    }
    return render(request, 'marketplace/product_detail.html', context)


def products(request):
    """Display products with search, filter, and pagination functionality"""
    query = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    sort_by = request.GET.get('sort', 'newest')
    
    products_list = Product.objects.filter(is_active=True)
    
    # Search
    if query:
        products_list = products_list.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    
    # Filter by category
    if category_id:
        products_list = products_list.filter(category_id=category_id)
    
    # Sorting
    if sort_by == 'price_low':
        products_list = products_list.order_by('price')
    elif sort_by == 'price_high':
        products_list = products_list.order_by('-price')
    elif sort_by == 'name':
        products_list = products_list.order_by('name')
    else:  # newest
        products_list = products_list.order_by('-created_at')
    
    # Pagination - 16 products per page (4x4 grid)
    paginator = Paginator(products_list, 16)
    page = request.GET.get('page', 1)
    
    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)
    
    categories = Category.objects.all()
    
    context = {
        'products': products_page,
        'categories': categories,
        'search_query': query,
        'category_id': category_id,
        'sort_by': sort_by,
        'paginator': paginator,
    }
    return render(request, 'marketplace/products.html', context)


@login_required
def add_to_cart(request, product_id):
    """Add product to cart"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f'{product.name} added to cart!')
    return redirect('cart')


@login_required
def cart_view(request):
    """Display shopping cart"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    context = {
        'cart': cart,
    }
    return render(request, 'marketplace/cart.html', context)


@login_required
@require_POST
def update_cart(request, item_id):
    """Update cart item quantity"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    action = request.POST.get('action')
    
    if action == 'increase':
        cart_item.quantity += 1
        cart_item.save()
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    elif action == 'remove':
        cart_item.delete()
    
    return redirect('cart')


@login_required
def checkout(request):
    """Checkout page"""
    cart = get_object_or_404(Cart, user=request.user)
    
    if not cart.items.exists():
        messages.warning(request, 'Your cart is empty!')
        return redirect('products')
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Create order
            order = Order.objects.create(
                user=request.user,
                full_name=form.cleaned_data['full_name'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone'],
                shipping_address=form.cleaned_data['shipping_address'],
                shipping_city=form.cleaned_data['shipping_city'],
                shipping_state=form.cleaned_data['shipping_state'],
                shipping_postal_code=form.cleaned_data['shipping_postal_code'],
                shipping_country=form.cleaned_data['shipping_country'],
                subtotal=cart.subtotal,
                shipping_fee=cart.shipping_fee,
                total_price=cart.total,
                notes=form.cleaned_data.get('notes', ''),
            )
            
            # Create order items
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    product_name=cart_item.product.name,
                    product_price=cart_item.product.price,
                    quantity=cart_item.quantity,
                    total_price=cart_item.total_price,
                )
            
            # Clear cart
            cart.items.all().delete()
            
            # Redirect to payment
            return redirect('payment', order_id=order.id)
    else:
        # Pre-fill form with user profile data
        profile = request.user.profile
        initial_data = {
            'full_name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
            'phone': profile.phone,
            'shipping_address': profile.shipping_address,
            'shipping_city': profile.shipping_city,
            'shipping_state': profile.shipping_state,
            'shipping_postal_code': profile.shipping_postal_code,
            'shipping_country': profile.shipping_country,
        }
        form = CheckoutForm(initial=initial_data)
    
    context = {
        'cart': cart,
        'form': form,
    }
    return render(request, 'marketplace/checkout.html', context)


@login_required
def payment(request, order_id):
    """Payment page with Paystack integration"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Paystack public key
    paystack_public_key = config('PAYSTACK_PUBLIC_KEY', default='')
    
    context = {
        'order': order,
        'paystack_public_key': paystack_public_key,
        'amount': int(order.total_price * 100),  # Convert to kobo
    }
    return render(request, 'marketplace/payment.html', context)


@login_required
def verify_payment(request, order_id):
    """Verify Paystack payment"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    reference = request.GET.get('reference')
    
    if not reference:
        messages.error(request, 'Payment reference not found!')
        return redirect('payment', order_id=order.id)
    
    # Verify payment with Paystack
    paystack_secret_key = config('PAYSTACK_SECRET_KEY', default='')
    headers = {
        'Authorization': f'Bearer {paystack_secret_key}',
    }
    
    try:
        response = requests.get(
            f'https://api.paystack.co/transaction/verify/{reference}',
            headers=headers
        )
        response_data = response.json()
        
        if response_data['status'] and response_data['data']['status'] == 'success':
            # Update order
            order.payment_reference = reference
            order.payment_status = 'paid'
            order.status = 'processing'
            order.save()
            
            messages.success(request, 'Payment successful! Your order is being processed.')
            return redirect('order_success', order_id=order.id)
        else:
            messages.error(request, 'Payment verification failed!')
            return redirect('payment', order_id=order.id)
    
    except Exception as e:
        messages.error(request, 'An error occurred while verifying payment.')
        return redirect('payment', order_id=order.id)


@login_required
def order_success(request, order_id):
    """Order success page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
    }
    return render(request, 'marketplace/order_success.html', context)


@login_required
def user_orders(request):
    """Display user's orders"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'marketplace/user_orders.html', context)


@login_required
def order_detail(request, order_id):
    """Display order details"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
    }
    return render(request, 'marketplace/order_detail.html', context)


@login_required
def add_to_wishlist(request, product_id):
    """Add/remove product from wishlist"""
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    if not created:
        wishlist_item.delete()
        messages.info(request, f'{product.name} removed from wishlist.')
    else:
        messages.success(request, f'{product.name} added to wishlist!')
    
    return redirect('product_detail', product_id=product.id)


@login_required
def view_wishlist(request):
    """Display user's wishlist"""
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    
    context = {
        'wishlist_items': wishlist_items,
    }
    return render(request, 'marketplace/wishlist.html', context)


@login_required
def profile(request):
    """Display user profile"""
    context = {
        'profile': request.user.profile,
    }
    return render(request, 'marketplace/profile.html', context)


@login_required
def edit_profile(request):
    """Edit user profile"""
    profile = request.user.profile
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
    
    context = {
        'form': form,
    }
    return render(request, 'marketplace/edit_profile.html', context)


@login_required
def submit_review(request, product_id):
    """Submit product review"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductReviewForm(request.POST)
        if form.is_valid():
            review, created = ProductReview.objects.update_or_create(
                product=product,
                user=request.user,
                defaults={
                    'rating': form.cleaned_data['rating'],
                    'comment': form.cleaned_data['comment'],
                }
            )
            
            if created:
                messages.success(request, 'Review submitted successfully!')
            else:
                messages.success(request, 'Review updated successfully!')
            
            return redirect('product_detail', product_id=product.id)
    
    return redirect('product_detail', product_id=product.id)


# Vendor views
@login_required
def vendor_dashboard(request):
    """Enhanced vendor dashboard with sales analytics"""
    try:
        vendor = request.user.vendor
    except Vendor.DoesNotExist:
        messages.warning(request, 'You need to register as a vendor first.')
        return redirect('homepage')
    
    # Get all vendor products
    products = vendor.products.all().order_by('-created_at')
    
    # Get vendor orders (orders containing vendor's products)
    vendor_order_items = OrderItem.objects.filter(
        product__vendor=vendor
    ).select_related('order', 'product')
    
    # Calculate statistics
    total_products = products.count()
    active_products = products.filter(is_active=True).count()
    out_of_stock = products.filter(stock=0).count()
    
    # Sales statistics
    paid_orders = vendor_order_items.filter(order__payment_status='paid')
    total_revenue = paid_orders.aggregate(total=Sum('total_price'))['total'] or 0
    total_orders = paid_orders.values('order').distinct().count()
    
    # Recent orders
    recent_orders = vendor_order_items.filter(
        order__payment_status='paid'
    ).order_by('-order__created_at')[:10]
    
    # Pending orders
    pending_orders = vendor_order_items.filter(
        order__status__in=['pending', 'processing']
    ).order_by('-order__created_at')[:5]
    
    # Monthly sales (last 6 months)
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_sales = []
    for i in range(6):
        month_start = timezone.now() - timedelta(days=30 * (5 - i))
        month_end = timezone.now() - timedelta(days=30 * (4 - i))
        month_revenue = paid_orders.filter(
            order__created_at__gte=month_start,
            order__created_at__lt=month_end
        ).aggregate(total=Sum('total_price'))['total'] or 0
        monthly_sales.append({
            'month': month_start.strftime('%b'),
            'revenue': float(month_revenue)
        })
    
    # Top selling products
    top_products = products.annotate(
        total_sold=Count('orderitem', filter=Q(orderitem__order__payment_status='paid'))
    ).order_by('-total_sold')[:5]
    
    # Low stock products
    low_stock_products = products.filter(stock__lte=5, stock__gt=0).order_by('stock')[:5]
    
    # Average rating
    average_rating = ProductReview.objects.filter(
        product__vendor=vendor
    ).aggregate(avg=Avg('rating'))['avg'] or 0
    
    # Handle product upload
    if request.method == 'POST':
        form = ProductUploadForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = vendor
            product.save()
            messages.success(request, f'Product "{product.name}" uploaded successfully!')
            return redirect('vendor_dashboard')
    else:
        form = ProductUploadForm()
    
    context = {
        'vendor': vendor,
        'products': products,
        'total_products': total_products,
        'active_products': active_products,
        'out_of_stock': out_of_stock,
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'recent_orders': recent_orders,
        'pending_orders': pending_orders,
        'monthly_sales': monthly_sales,
        'top_products': top_products,
        'low_stock_products': low_stock_products,
        'average_rating': average_rating,
        'form': form,
        'categories': Category.objects.all(),
    }
    return render(request, 'marketplace/vendor_dashboard.html', context)


@login_required
def vendor_orders(request):
    """View all vendor orders"""
    try:
        vendor = request.user.vendor
    except Vendor.DoesNotExist:
        messages.warning(request, 'You need to be a vendor to access this page.')
        return redirect('homepage')
    
    # Get all orders containing vendor's products
    order_items = OrderItem.objects.filter(
        product__vendor=vendor
    ).select_related('order', 'product').order_by('-order__created_at')
    
    # Group by order
    orders_dict = {}
    for item in order_items:
        order_id = item.order.id
        if order_id not in orders_dict:
            orders_dict[order_id] = {
                'order': item.order,
                'items': [],
                'vendor_total': 0
            }
        orders_dict[order_id]['items'].append(item)
        orders_dict[order_id]['vendor_total'] += item.total_price
    
    context = {
        'orders': orders_dict.values(),
        'vendor': vendor,
    }
    return render(request, 'marketplace/vendor_orders.html', context)


@login_required
def vendor_analytics(request):
    """Vendor analytics page"""
    try:
        vendor = request.user.vendor
    except Vendor.DoesNotExist:
        messages.warning(request, 'You need to be a vendor to access this page.')
        return redirect('homepage')
    
    # Date range filter
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Sales over time
    daily_sales = OrderItem.objects.filter(
        product__vendor=vendor,
        order__payment_status='paid',
        order__created_at__gte=start_date
    ).extra(
        select={'day': 'date(order__created_at)'}
    ).values('day').annotate(
        revenue=Sum('total_price'),
        orders=Count('order', distinct=True)
    ).order_by('day')
    
    # Product performance
    product_performance = vendor.products.annotate(
        views=Count('id'),  # You can add view tracking later
        sales=Count('orderitem', filter=Q(orderitem__order__payment_status='paid')),
        revenue=Sum('orderitem__total_price', filter=Q(orderitem__order__payment_status='paid'))
    ).order_by('-revenue')
    
    context = {
        'vendor': vendor,
        'daily_sales': daily_sales,
        'product_performance': product_performance,
        'days': days,
    }
    return render(request, 'marketplace/vendor_analytics.html', context)


# Authentication views
def register(request):
    """User registration with proper vendor creation"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Save the user
                    user = form.save()
                    
                    # Update profile with additional info
                    profile = user.profile
                    if form.cleaned_data.get('profile_picture'):
                        profile.profile_picture = form.cleaned_data['profile_picture']
                    if form.cleaned_data.get('bio'):
                        profile.bio = form.cleaned_data['bio']
                    profile.save()
                    
                    # Create vendor if user type is vendor
                    user_type = form.cleaned_data.get('user_type')
                    if user_type == 'vendor':
                        vendor = Vendor.objects.create(
                            user=user,
                            name=user.get_full_name() or user.username,
                            contact_email=user.email,
                            location='',  # Will be set later in profile
                            description=form.cleaned_data.get('bio', '')
                        )
                        messages.success(
                            request, 
                            f'Vendor account created successfully! Welcome {user.username}. '
                            'Please complete your vendor profile to start selling.'
                        )
                    else:
                        messages.success(
                            request, 
                            f'Account created successfully! Welcome {user.username}. '
                            'You can now start shopping.'
                        )
                    
                    return redirect('login')
                    
            except IntegrityError as e:
                messages.error(request, 'An error occurred during registration. Please try again.')
                print(f"Registration error: {e}")
    else:
        form = UserRegistrationForm()
    
    context = {
        'form': form,
    }
    return render(request, 'marketplace/register.html', context)


def login_view(request):
    """User login"""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, 'Login successful!')
                next_url = request.GET.get('next', 'homepage')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    
    context = {
        'form': form,
    }
    return render(request, 'marketplace/login.html', context)


def logout_view(request):
    """User logout"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('homepage')


# Static pages
def about(request):
    return render(request, 'marketplace/about.html')

def contact(request):
    return render(request, 'marketplace/contact.html')

def privacy_policy(request):
    return render(request, 'marketplace/privacy_policy.html')

def terms_of_service(request):
    return render(request, 'marketplace/terms_of_service.html')