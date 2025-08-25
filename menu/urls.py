from django.urls import path
from . import views

app_name = 'menu'

urlpatterns = [
    # Main page: displays menu, handles adding categories and products
    path('', views.menu_view, name='menu_view'),
    
    # URL for editing a category (e.g., /menu/category/5/edit/)
    path('category/<int:category_id>/edit/', views.edit_category, name='edit_category'),
    
    # URL for deleting a category
    path('category/<int:category_id>/delete/', views.delete_category, name='delete_category'),
    
    # URL for editing a product
    path('product/<int:product_id>/edit/', views.edit_product, name='edit_product'),
    
    # URL for deleting a product
    path('product/<int:product_id>/delete/', views.delete_product, name='delete_product'),
]