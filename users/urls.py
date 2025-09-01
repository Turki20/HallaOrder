from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('sign_up/', views.sign_up_view, name='sign_up_view'),
    path('login/', views.log_in_view, name='log_in_view'),
    path('logout/', views.logout_view, name='logout_view'),
    path('all_users/', views.all_users, name='all_users'),
    path('edit_user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete/', views.delete_user, name='delete_user'),
    
    # customer
    path('customer_sign_up/<slug:slug>/', views.customer_sign_up, name='customer_sign_up'),
    path('customer_login/<slug:slug>/', views.customer_login, name='customer_login'),
    path('customer_logout_view/<slug:slug>/', views.customer_logout_view, name='customer_logout_view'),

]
