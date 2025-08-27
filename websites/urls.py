from django.urls import path
from . import views

app_name = "websites"

urlpatterns = [
    path("s/<slug:slug>/", views.menu_view, name="public"),

    path("s/<slug:slug>/menu/", views.menu_view, name="menu"),
    path("s/<slug:slug>/p/<int:pk>/", views.product_detail, name="product"),
    path("s/<slug:slug>/cart/", views.cart_view, name="cart"),
    path("s/<slug:slug>/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),

    path("websites/preview/<int:pk>/", views.preview_by_pk, name="preview"),
    path("websites/preview/", views.preview_my_site, name="preview_my_site"),
]
