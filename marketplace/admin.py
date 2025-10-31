from django.contrib import admin
from .models import Category, Product, Vendor, ProductReview, Order, UserProfile, Wishlist

admin.site.site_header = "TradeSphere Administration"
admin.site.site_title = "TradeSphere Admin Portal"
admin.site.index_title = "Welcome to TradeSphere Admin"

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'created_at', 'updated_at', 'vendor')
    list_filter = ('category', 'vendor')
    search_fields = ('name', 'description')

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_email', 'contact_phone', 'website', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'contact_email')

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('product', 'rating')
    search_fields = ('user__username', 'product__name', 'comment')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'total_price', 'created_at')
    list_filter = ('user', 'product')
    search_fields = ('user__username', 'product__name')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio')
    search_fields = ('user__username',)

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'added_at')
    list_filter = ('user', 'product')
    search_fields = ('user__username', 'product__name')
