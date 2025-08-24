from django.urls import path
from . import views

# This defines a namespace for your app's URLs.
# It's used in templates like {% url 'menu:menu' %}
app_name = 'menu'

urlpatterns = [
    # This single URL will handle everything:
    # - Displaying the menu (GET request)
    # - Adding a new category (POST request)
    # - Adding a new product (POST request)
    path('', views.menu_view, name='menu_view'),
    
    # You can add URLs for editing and deleting later, for example:
    # path('product/<int:product_id>/delete/', views.delete_product_view, name='delete_product'),
]