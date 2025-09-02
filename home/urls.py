from django.urls import path
from . import views as home

app_name = 'home'

urlpatterns = [
    path('', home.index_view, name='index_view'),
    path('create_restaurant_identity/', home.create_restaurant_identity, name='create_restaurant_identity'),
    path('subscriptionplan/', home.subscriptionplan_view, name='subscriptionplan_view'),
    path('restaurant_identity/', home.restaurant_identity, name='restaurant_identity'),
    path('add_food_plate/', home.add_food_plate, name='add_food_plate'),
    path('add_branch_view/', home.add_branch_view, name='add_branch_view'),
    path('settings/', home.settings_view, name='settings'),
]
