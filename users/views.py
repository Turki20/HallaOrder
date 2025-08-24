from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.http import HttpRequest
from .models import Profile
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import authenticate, login, logout
# Create your views here.

def sign_up_view(request:HttpRequest):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        phone = request.POST.get("phone")

        if password1 != password2:
            messages.error(request, "كلمتا المرور غير متطابقتين.", 'alert-danger')
            return redirect("users:sign_up_view")

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password1,
                )

                profile = Profile.objects.create(
                    phone=phone,
                    role='RestaurantOwner',
                    user=user  
                )

                messages.success(request, "تم إنشاء الحساب بنجاح", 'alert-success')
                return redirect("users:sign_up_view")

        except Exception as e:
            messages.error(request, f"حدث خطأ: {e}", 'alert-danger')
            return redirect("users:sign_up_view")

    return render(request, 'users/sign_up.html', {})

def log_in_view(request:HttpRequest):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # messages.success(request, f"مرحباً {user.username}", 'alert-success')
            return redirect("home:index_view") 
        else:
            messages.error(request, "اسم المستخدم أو كلمة المرور غير صحيحة", 'alert-danger')
            return redirect("users:log_in_view")

    return render(request, 'users/login.html', {})


def logout_view(request:HttpRequest):
    if request.user.is_authenticated:
        logout(request)
    return redirect("home:index_view")