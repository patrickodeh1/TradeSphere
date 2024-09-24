from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.homepage, name='homepage'),  # Homepage
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),  # Product detail page
    path('products/', views.products, name='products'),
    path('vendors/<int:pk>/', views.VendorDetailView.as_view(), name='vendor_detail'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('order/<int:product_id>/', views.place_order, name='place_order'),
    path('orders/', views.user_orders, name='user_orders'),
    path('product/<int:product_id>/review/', views.submit_review, name='submit_review'),
    path('category/<int:category_id>/', views.category_products, name='category_products'),
    path('order_success/', views.order_success, name='order_success'),
    path('wishlist/', views.view_wishlist, name='view_wishlist'),
    path('add_to_wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('vendor/dashboard/', views.vendor_dashboard, name='vendor_dashboard'),
]
