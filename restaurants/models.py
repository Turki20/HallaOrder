from django.db import models
from django.contrib.auth.models import User

# Create your models here.


# Subscription Plans
class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    features = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# Restaurants
class Restaurant(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=140, unique=True, null=True, blank=True)
    description = models.TextField()
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name="restaurants")
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name


# Branches
class Branch(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="branches")
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=255)
    qr_code = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return  self.name