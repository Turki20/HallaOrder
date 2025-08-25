from django.urls import path
from . import views

urlpatterns = [
    path("subscriptions/", views.subscription_plans_list, name="subscription_plans"), 
    path("restaurants/", views.restaurants_list, name="restaurants"),
    path('restaurants/add/', views.restaurant_add, name='restaurants_add'),
    path('restaurants/<int:pk>/edit/', views.restaurant_edit, name='restaurants_edit'),
    path('restaurants/<int:pk>/delete/', views.restaurant_delete, name='restaurants_delete'),
    path("branches/", views.branches_list, name="branches"),
    path('branches/add/', views.branch_create, name='branch_add'),
    path('branches/<int:pk>/edit/', views.branch_update, name='branch_edit'),
    path('branches/<int:pk>/delete/', views.branch_delete, name='branch_delete'),
]
