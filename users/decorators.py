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
        
        if hasattr(user, 'profile') and user.profile.role == 'RestaurantOwner':
            return view_func(request, *args, **kwargs)

        messages.error(request, "غير مصرح لك بالوصول إلى هذه الصفحة.", 'alert-danger')
        return redirect('orders:order_board') 

    return _wrapped_view
