from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

# Create your views here.

def dashboard_view(request: HttpRequest) -> HttpResponse:
    context={
       "current_page": "reports:dashboard"
    }
    return render(request, "reports/dashboard.html" , context)

