from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('sign_up/', views.sign_up_view, name='sign_up_view'),
    path('login/', views.log_in_view, name='log_in_view'),
    path('logout/', views.logout_view, name='logout_view'),
]
