from django.shortcuts import render, redirect, get_object_or_404
from .models import SubscriptionPlan, Restaurant, Branch
from .forms import RestaurantForm ,BranchForm
from django.contrib.auth.models import User
from django.contrib import messages
from websites.models import Website
from .forms import WebsiteForm
from users.decorators import restaurant_owner_required
from dotenv import load_dotenv
import os
load_dotenv()  

# عرض باقات الاشتراك
@restaurant_owner_required
def subscription_plans_list(request):
    subscription_plans = SubscriptionPlan.objects.all()
    context = {
        "subscription_plans": subscription_plans,
        "current_page": "subscription_plans",  # لتحديد الصفحة الحالية
    }
    return render(request, "restaurants/Subscription_Plans.html", context)

# عرض المطاعم
@restaurant_owner_required
def restaurants_list(request):
    # التحقق هل المطعم فعال ام لم يتم تفعيلة
    try:
        if not request.user.restaurants.is_active:
            messages.error(request, "الرجاء اكمال معلومات المطعم للوصول للوحة التحكم", 'alert-danger')
            return redirect('home:create_restaurant_identity')
    except:
            messages.error(request, "الرجاء اكمال معلومات المطعم للوصول للوحة التحكم", 'alert-danger')
            return redirect('home:create_restaurant_identity')
    
    restaurant = Restaurant.objects.get(pk = request.user.restaurants.id)
    website = Website.objects.get(restaurant=restaurant)
    
    if request.method == 'POST':
        form = WebsiteForm(request.POST, request.FILES, instance=website)
        if form.is_valid():
            form.save()
            return redirect('restaurants')  # استبدل باسم URL المناسب
    else:
        form = WebsiteForm(instance=website)
        
    context = {
        "restaurant": restaurant,
        'website': website,
        'form': form,
        "current_page": "restaurants",  
    }
    return render(request, "restaurants/restaurant_list.html", context)

# Add a new restaurant
@restaurant_owner_required
def restaurant_add(request):
    if request.method == 'POST':
        form = RestaurantForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('restaurants')
    else:
        form = RestaurantForm()
    return render(request, 'restaurants/restaurant_form.html', {'form': form, 'title': 'اضافة مطعم'})

# Edit a restaurant
@restaurant_owner_required
def restaurant_edit(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    if request.method == 'POST':
        form = RestaurantForm(request.POST, instance=restaurant)
        if form.is_valid():
            form.save()
            return redirect('restaurants')
    else:
        form = RestaurantForm(instance=restaurant)
    return render(request, 'restaurants/restaurant_form.html', {'form': form, 'title': 'Edit Restaurant'})

# Delete a restaurant
@restaurant_owner_required
def restaurant_delete(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    if request.method == 'POST':
        restaurant.delete()
        return redirect('restaurants')
    return render(request, 'restaurants/restaurant_confirm_delete.html', {'object': restaurant})

# عرض الفروع
@restaurant_owner_required
def branches_list(request):
    branches = Branch.objects.select_related("restaurant").filter(restaurant = request.user.restaurants)
    context = {
        "branches": branches,
        "current_page": "branches",  
    }
    return render(request, "restaurants/Branches.html", context)

@restaurant_owner_required
def branch_create(request):
    if request.method == "POST":
        form = BranchForm(request.POST)
        if form.is_valid():
            branch = form.save(commit=False)
            branch.restaurant = request.user.restaurants
            branch.save()
            return redirect('branches')  
    else:
        form = BranchForm()
        google_map_key = os.getenv('google_map_key', "")

    return render(request, "restaurants/Branch_Form.html", {
        "form": form, 
        "title": "إضافة فرع",
        'google_map_key':google_map_key
    })

# تعديل فرع موجود
@restaurant_owner_required
def branch_update(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    if request.method == "POST":
        form = BranchForm(request.POST, instance=branch)
        if form.is_valid():
            form.save()
            return redirect('branches')
    else:
        form = BranchForm(instance=branch)
    google_map_key = os.getenv('google_map_key', "")
    return render(request, "restaurants/Branch_Form.html", {"form": form, "title": "تعديل فرع", 'google_map_key': google_map_key})

# حذف فرع
@restaurant_owner_required
def branch_delete(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    if request.method == "POST":
        branch.delete()
        return redirect('branches')
    return render(request, "restaurants/Branch_Confirm_Delete.html", {"branch": branch})


