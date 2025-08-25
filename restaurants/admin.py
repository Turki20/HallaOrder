from django.contrib import admin
from .models import Restaurant
from .models import SubscriptionPlan, Restaurant, Branch 

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    search_fields = ("name", "slug")

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price", "created_at", "updated_at")


