from django.contrib import admin

from .models import SubscriptionPlan, Restaurant, Branch
# Register your models here.

admin.site.register(SubscriptionPlan)
admin.site.register(Branch)
admin.site.register(Restaurant)
