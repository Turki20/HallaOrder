# menu/urls.py

from django.urls import path
from . import views

app_name = 'menu'

urlpatterns = [
    # Main page
    path('', views.menu_view, name='menu_view'),
    
    # Category URLs
    path('category/<int:category_id>/edit/', views.edit_category, name='edit_category'),
    path('category/<int:category_id>/delete/', views.delete_category, name='delete_category'),
    
    # Product URLs
    path('product/<int:product_id>/edit/', views.edit_product, name='edit_product'),
    path('product/<int:product_id>/delete/', views.delete_product, name='delete_product'),
    path('product/<int:product_id>/toggle/', views.toggle_product_availability, name='toggle_product'),
    
    # Product Image Gallery URLs
    path('product/image/<int:image_id>/set-cover/', views.set_cover_image, name='set_cover_image'),
    path('product/image/<int:image_id>/delete/', views.delete_product_image, name='delete_product_image'),

    # Options & Add-ons URLs
    path('options/<int:group_id>/edit/', views.edit_option_group, name='edit_option_group'),
    path('options/<int:group_id>/delete/', views.delete_option_group, name='delete_option_group'),

    # NEW URLS FOR MEAL MANAGEMENT
    path('meals/', views.meal_management, name='meal_management'),
    path('meals/create/', views.create_or_edit_meal, name='create_meal'),
    path('meals/<int:meal_id>/edit/', views.create_or_edit_meal, name='edit_meal'),
    path('meals/<int:meal_id>/delete/', views.delete_meal, name='delete_meal'),
]