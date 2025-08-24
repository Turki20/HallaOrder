from django.shortcuts import render
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required

# Create your views here.


def index_view(request:HttpRequest):
    
    return render(request, 'home/index.html')

@login_required(login_url='/users/sign_up/')
def create_restaurant_identity(request:HttpRequest):
    
    return render(request, 'home/create_restaurant_identity.html')