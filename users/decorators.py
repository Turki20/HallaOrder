# users/decorators.py

from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def restaurant_owner_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            messages.error(request, "يجب تسجيل الدخول أولاً.", 'alert-danger')
            return redirect('users:log_in_view')
        
        if hasattr(user, 'profile'):
            if user.profile.role == 'RestaurantOwner':
                return view_func(request, *args, **kwargs)
            
            if user.profile.role == 'Admin':
                return redirect('home:index_view')
            
            if user.profile.role == 'Customer':
                messages.error(request, "هذه الصفحة مخصصة لصاحب المطعم اذا اردت تسجيل حساب لديينا الرجاء التسجيل هنا", 'alert-danger')
                return redirect('users:sign_up_view')
            
            if user.profile.role == 'Cashier':
                messages.error(request, "غير مصرح لك بالوصول إلى هذه الصفحة.", 'alert-danger')
                return redirect('orders:order_board')
        

        messages.error(request, "غير مصرح لك بالوصول إلى هذه الصفحة.", 'alert-danger')
        return redirect('orders:order_board') 

    return _wrapped_view
