from django.db import models
# from restaurants.models import Branch
# Create your models here.


# Employees
# class Employee(models.Model):
#     ROLE_CHOICES = [
#         ('Cashier', 'Cashier'),
#         ('KitchenStaff', 'Kitchen Staff'),
#     ]

#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="employees")
#     role = models.CharField(max_length=20, choices=ROLE_CHOICES)
#     permissions = models.TextField(blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)