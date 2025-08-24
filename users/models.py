from django.db import models
from restaurants.models import Branch
from django.contrib.auth.models import User
# Create your models here.

# Users
class Profile(models.Model):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('RestaurantOwner', 'Restaurant Owner'),
        ('Staff', 'Staff'),
        ('Customer', 'Customer'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=10)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# Employees
class Employee(models.Model):
    ROLE_CHOICES = [
        ('Cashier', 'Cashier'),
        ('KitchenStaff', 'Kitchen Staff'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="employees")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    permissions = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)