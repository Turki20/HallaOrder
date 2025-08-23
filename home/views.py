from django.shortcuts import render
from django.http import HttpRequest
# Create your views here.


def index_view(request:HttpRequest):
    
    return render(request, 'home/base.html')