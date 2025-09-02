from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from restaurants.models import SubscriptionPlan, Restaurant, Branch
from menu.models import Product, Category, ProductImage
from django.contrib import messages
from django.db import transaction
from websites.models import Website
from django.contrib.auth.models import User
from users.decorators import restaurant_owner_required
from dotenv import load_dotenv
import os
load_dotenv()  

# Create your views here.

# سوي ديكوريتر ان المستخدم يكون صاحب مطعم
def index_view(request:HttpRequest):
    
    return render(request, 'home/index.html')


def about_view(request:HttpRequest):
    return render(request, 'home/about.html')


def services_view(request:HttpRequest):
    return render(request, 'home/services.html')


def clients_view(request:HttpRequest):
    return render(request, 'home/clients.html')


def faq_view(request:HttpRequest):
    return render(request, 'home/faq.html')

@login_required(login_url='/users/login/')
@restaurant_owner_required
def subscriptionplan_view(request:HttpRequest):
    if request.method == 'POST':
        request.session['subscriptionplan_id'] = request.POST['subscriptionplan']
      
    # # اذا المستخدم لديه مطعم بالفعل تم تسجيلة  
    # try:
    #     if request.user.restaurants:
    #         return redirect('home:create_restaurant_identity')
    # except:
    #     pass
    
    subscription_plan_search = Restaurant.objects.filter(owner = request.user)
    if len(subscription_plan_search) > 0:
        return redirect('restaurants')
        
    subscriptionplan_data = request.session.get('subscriptionplan_id', None)
    if subscriptionplan_data is not None:
        return redirect('home:create_restaurant_identity')
    
    subscriptionPlan = SubscriptionPlan.objects.all()
    return render(request, 'home/subscriptionplan.html', {'subscriptionPlan':subscriptionPlan})

@login_required(login_url='/users/login/')
@restaurant_owner_required
def create_restaurant_identity(request:HttpRequest):
    # لازم قبل يسوي انشاء للمطعم يختار الباقه
    subscriptionplan_data = request.session.get('subscriptionplan_id', None)
    if subscriptionplan_data is None:
        return redirect('home:subscriptionplan_view')
    
    return render(request, 'home/create_restaurant_identity.html')


@login_required(login_url='/users/login/')
@restaurant_owner_required
def restaurant_identity(request:HttpRequest):
    # لازم قبل يسوي انشاء للمطعم يختار الباقه
    subscriptionplan_data = request.session.get('subscriptionplan_id', None)
    if subscriptionplan_data is None:
        return redirect('home:subscriptionplan_view')
    
    # تحقق اذا كان المستخدم قد انشئ مطعم ولا باقي 
    # تحقق اذا كان المستخدم قد انشئ مطعم
    if Restaurant.objects.filter(owner=request.user).exists():
        messages.success(request, "تم انشاء هوية المطعم مسبقًا", 'alert-success')
        return redirect('home:create_restaurant_identity')
        
    if request.method == 'POST':
        restaurant_name = request.POST['restaurant_name']
        restaurant_desc = request.POST['restaurant_desc']
        restaurant_logo = request.FILES['restaurant_logo']
        primary_color = request.POST['primary_color']
        secondary_color = request.POST.get('secondary_color', '#FFFFFF')
        
        if not restaurant_name or not restaurant_desc or not restaurant_logo or not primary_color:
            messages.error(request, "الرجاء تعبئة جميع الحقول المطلوبة", 'alert-danger')
            return render(request, 'home/restaurant_identity.html')
        
        with transaction.atomic():
            restaurant = Restaurant(
                name = restaurant_name,
                description = restaurant_desc,
                owner = request.user,
                subscription_plan = SubscriptionPlan.objects.get(pk = subscriptionplan_data),
                slug = restaurant_name
            )
            
            restaurant.save()
            
            website = Website(
                restaurant = restaurant,
                custom_colors = primary_color,
                secondary_color = secondary_color,
                logo = restaurant_logo,
                slug = restaurant.id # غيرها حسب رغبتك
            )
            
            website.save()
        
        messages.success(request, "تم إنشاء هوية المطعم بنجاح", 'alert-success')
        return redirect('home:create_restaurant_identity')
            
    return render(request, 'home/restaurant_identity.html', {})

@login_required(login_url='/users/login/')
@restaurant_owner_required
def add_food_plate(request:HttpRequest):
    # تحقق يجب ان ينشئ المطعم اولا
    try:
        request.user.restaurants
    except:
        messages.error(request, "يجب انشاء هوية المطعم اولا", 'alert-danger')
        return redirect('home:create_restaurant_identity')
    
    if len(request.user.restaurants.category_set.all()) > 0:
        messages.success(request, "تم اضافة طبق مسبقًا", 'alert-success')
        return redirect('home:create_restaurant_identity')
    
    if request.method == "POST":
        category_name = request.POST.get("category_name", "").strip()
        category_desc = request.POST.get("category_desc", "").strip()
        dish_name = request.POST.get("dish_name", "").strip()
        dish_desc = request.POST.get("dish_desc", "").strip()
        dish_price = request.POST.get("dish_price", "").strip()
        dish_image = request.FILES.get("dish_image", None)

        # تحقق أساسي من المدخلات
        if not category_name:
            messages.error(request, "اسم الفئة مطلوب", 'alert-danger')
            return redirect('home:add_food_plate')

        if not dish_name:
            messages.error(request, "اسم الطبق مطلوب", 'alert-danger')
            return redirect('home:add_food_plate')

        if not dish_price or not dish_price.replace(".", "", 1).isdigit():
            messages.error(request, "الرجاء إدخال سعر صالح", 'alert-danger')
            return redirect('home:add_food_plate')

        if dish_image:
            allowed_types = ["image/png", "image/jpeg", "image/webp", "image/svg+xml"]
            if dish_image.content_type not in allowed_types:
                messages.error(request, "نوع الصورة غير مسموح. الأنواع المسموحة: PNG, JPG, WEBP, SVG", 'alert-danger')
                return redirect('home:add_food_plate')

        with transaction.atomic():
            category = Category(
                restaurant = request.user.restaurants,
                name = category_name,
                description = category_desc
            )

            category.save()

            # إنشاء الطبق
            dish = Product.objects.create(
                name=dish_name,
                description=dish_desc,
                price=float(dish_price),
                category=category,
            )
            
            product_image = ProductImage.objects.create(
                product = dish,
                image = dish_image,
                is_cover = True
            )

        messages.success(request, f"تم إضافة الطبق '{dish.name}' بنجاح", 'alert-success')
        # restaurant = Restaurant.objects.get(pk = request.user.restaurants.id)
        # restaurant.is_active = True
        # restaurant.save()
        # return redirect('restaurants')
        return redirect('home:create_restaurant_identity')

    return render(request, 'home/add_food_plate.html', {})

@login_required(login_url='/users/login/')
@restaurant_owner_required
def add_branch_view(request:HttpRequest):
    try:
        request.user.restaurants
    except:
        messages.error(request, "يجب انشاء هوية المطعم اولا", 'alert-danger')
        return redirect('home:create_restaurant_identity')
    
    if request.method == "POST":
        branch_name = request.POST.get("name", "").strip()
        branch_address = request.POST.get("address", "").strip()

        if not branch_name:
            messages.error(request, "يجب إدخال اسم الفرع", 'alert-danger')
            return redirect("home:add_branch_view") 

        elif not branch_address:
            messages.error(request, "يجب إدخال عنوان الفرع", 'alert-danger')
            return redirect("home:add_branch_view") 
        
        else:
            # إنشاء الفرع
            Branch.objects.create(
                restaurant=request.user.restaurants,
                name=branch_name,
                address=branch_address
            )
            # messages.success(request, "تم إضافة الفرع بنجاح", 'alert-success')
            rest_id = request.user.restaurants.id
            restaurant = Restaurant.objects.get(pk = rest_id)
            restaurant.is_active = True
            restaurant.save()
            
            user = User.objects.get(pk = request.user.id)
            user.profile.restaurant = restaurant
            user.profile.save()
            return redirect('restaurants')
    
    google_map_key = os.getenv('google_map_key', "")
    return render(request, 'home/add_branch.html', {'google_map_key':google_map_key})


@login_required(login_url='/users/login/')
@restaurant_owner_required
def settings_view(request:HttpRequest):
    context = {
        "current_page": "home:settings",
    }
    return render(request, 'home/settings.html', context)