# menu/admin.py

from django.contrib import admin
from .models import Category, Product, ProductImage, OptionGroup, Option

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'is_cover')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'position')
    list_filter = ('restaurant',)
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'available')
    list_filter = ('category', 'available')
    search_fields = ('name', 'description')
    inlines = [ProductImageInline]
    # Use a better UI for ManyToMany fields
    filter_horizontal = ('option_groups',)

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_cover', 'uploaded_at')
    list_filter = ('is_cover', 'product__category__restaurant')

class OptionInline(admin.TabularInline):
    model = Option
    extra = 1
    ordering = ('position',)

@admin.register(OptionGroup)
class OptionGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'selection_type', 'is_required')
    list_filter = ('restaurant', 'selection_type', 'is_required')
    search_fields = ('name',)
    inlines = [OptionInline]