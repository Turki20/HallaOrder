from django.contrib import admin
from .models import Website

@admin.register(Website)
class WebsiteAdmin(admin.ModelAdmin):
    list_display = ("id", "restaurant", "slug", "theme", "updated_at")
    search_fields = ("restaurant__name", "slug")
