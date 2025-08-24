from django.urls import path
from . import views as home

app_name = 'home'

urlpatterns = [
    path('', home.index_view, name='index_view'),
    path('create_restaurant_identity/', home.create_restaurant_identity, name='create_restaurant_identity'),
]
