from django.urls import path
from . import views

app_name = "websites"

urlpatterns = [
    path("s/<slug:slug>/", views.menu_view, name="public"),
    path("s/<slug:slug>/menu/", views.menu_view, name="menu"),
    path("s/<slug:slug>/p/<int:product_id>/", views.product_detail, name="product_detail"),
    path("s/<slug:slug>/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("s/<slug:slug>/remove/<int:index>/", views.remove_from_cart, name="remove_from_cart"),
    path("s/<slug:slug>/save-meta/", views.save_cart_meta, name="save_cart_meta"),
    path("s/<slug:slug>/cart/", views.cart_view, name="cart"),

    path("websites/preview/<int:pk>/", views.preview_by_pk, name="preview"),
    path("websites/preview/", views.preview_my_site, name="preview_my_site"),
    
    path('order/save_dinein/', views.save_dinein_details, name='save_dinein_details'),
    path('order/save_pickup/', views.save_pickup_details, name='save_pickup_details'),
    path('order/save_delivery/', views.save_delivery_details, name='save_delivery_details'),
    
    path("s/<slug:slug>/my-orders/", views.user_orders, name="user_orders"),
    # path('order/confirm/', views.confirm_order, name='confirm_order'),
]