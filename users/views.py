from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import HttpRequest
from .models import Profile
# Create your views here.

def sign_up_view(request:HttpRequest):
    roles = Profile.ROLE_CHOICES
    return render(request, 'users/sign_up.html', {'roles':roles})