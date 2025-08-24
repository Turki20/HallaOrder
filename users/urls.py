from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('sign_up/', views.sign_up_view, name='sign_up_view'),
]
