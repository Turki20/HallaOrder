from django.db import models
from restaurants.models import Restaurant
# Create your models here.

# Website / Theme
class Website(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="websites")
    theme = models.CharField(max_length=100)
    custom_colors = models.CharField(max_length=255, blank=True, null=True)
    logo = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)