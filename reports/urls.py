from django.urls import path
from . import views

app_name= 'reports'

urlpatterns = [
      path("dashboard/", views.dashboard_view, name="dashboard"),
]