from django.urls import path
from . import views

app_name = "websites"
urlpatterns = [
    path("s/<slug:slug>/", views.site_home, name="site_home"),
    path("preview/<int:pk>/", views.preview, name="preview"),
   
]
