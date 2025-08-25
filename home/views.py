from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from restaurants.models import SubscriptionPlan
# Create your views here.

# سوي ديكوريتر ان المستخدم يكون صاحب مطعم

def index_view(request:HttpRequest):
    
    return render(request, 'home/index.html')


@login_required(login_url='/users/sign_up/')
def subscriptionplan_view(request:HttpRequest):
    if request.method == 'POST':
        request.session['subscriptionplan_id'] = request.POST['subscriptionplan']
    
    subscriptionplan_data = request.session.get('subscriptionplan_id', None)
    if subscriptionplan_data is not None:
        return redirect('home:create_restaurant_identity')
    
    subscriptionPlan = SubscriptionPlan.objects.all()
    return render(request, 'home/subscriptionplan.html', {'subscriptionPlan':subscriptionPlan})

@login_required(login_url='/users/sign_up/')
def create_restaurant_identity(request:HttpRequest):
    # لازم قبل يسوي انشاء للمطعم يختار الباقه
    subscriptionplan_data = request.session.get('subscriptionplan_id', None)
    if subscriptionplan_data is None:
        return redirect('home:subscriptionplan_view')
    
    return render(request, 'home/create_restaurant_identity.html')


@login_required(login_url='/users/sign_up/')
def restaurant_identity(request:HttpRequest):
    # لازم قبل يسوي انشاء للمطعم يختار الباقه
    subscriptionplan_data = request.session.get('subscriptionplan_id', None)
    if subscriptionplan_data is None:
        return redirect('home:subscriptionplan_view')
    
    return render(request, 'home/restaurant_identity.html', {})