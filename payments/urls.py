from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("quick-checkout/", views.quick_checkout, name="quick_checkout"),
    path("success/", views.success, name="success"),
    path("cancel/", views.cancel, name="cancel"),
    path("order-status/<int:order_id>/", views.public_order_status, name="public_order_status"),
    path("webhook/", views.stripe_webhook, name="stripe_webhook"),
]
