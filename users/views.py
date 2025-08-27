from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.http import HttpRequest
from .models import Profile
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from restaurants.models import Restaurant, Branch
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

@login_required(login_url='/users/login/')
def all_users(request:HttpRequest):
    # تحقق ان المستخدم عنده مطعم 
    restaurant = Restaurant.objects.get(pk=request.user.restaurants.id)
    branchs = restaurant.branches.all()
    all_users_in_restaurant = restaurant.profile_set.all().exclude(role='RestaurantOwner')
    all_users_in_restaurant_count = all_users_in_restaurant.count()
    BranchManager_count = restaurant.profile_set.filter(role='BranchManager').count()
    Cashier_count = restaurant.profile_set.filter(role='Cashier').count()
    
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        role = request.POST.get('role')
        branch_id = request.POST.get('branch')

        if not all([username, first_name, last_name, email, password, phone, role, branch_id]):
            messages.error(request, 'يرجى ملء جميع الحقول المطلوبة.', 'alert-danger')
            return redirect('users:all_users')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'البريد الإلكتروني مستخدم بالفعل.',  'alert-danger')
            return redirect('users:all_users')

        if not phone.isdigit() or len(phone) != 10:
            messages.error(request, 'رقم الجوال يجب أن يكون مكونًا من 10 أرقام.', 'alert-danger')
            return redirect('users:all_users')

        try:
            branch = Branch.objects.get(id=branch_id)
        except:
            messages.error(request, 'الفرع غير موجود.', 'alert-danger')
            return redirect('users:all_users')

        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password
            )

            Profile.objects.create(
                user=user,
                phone=phone,
                role=role,
                branch=branch,
                restaurant=branch.restaurant
            )

        messages.success(request, 'تم إنشاء المستخدم بنجاح.', 'alert-success')
        return redirect('users:all_users')
    
    print(all_users_in_restaurant)
    if request.method == 'POST':
        pass
    
    return render(request, 'users/users_list.html', {'branchs':branchs, 'all_users_in_restaurant':all_users_in_restaurant, 'all_users_in_restaurant_count':all_users_in_restaurant_count, 'BranchManager_count':BranchManager_count, 'Cashier_count':Cashier_count})

@login_required(login_url='/users/login/')
def edit_user(request:HttpRequest, user_id):
    if request.method == 'POST':
        pass
    
    user = User.objects.get(pk=user_id)
    return render(request, 'users/edit_user.html', {'user': user})