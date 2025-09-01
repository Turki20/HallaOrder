from orders.models import OrderStatus
from restaurants.models import Restaurant

REVENUE_STATUSES = (OrderStatus.DELIVERED,)

def get_user_restaurant(user):
    try:
        return user.restaurants
    except (Restaurant.DoesNotExist, AttributeError):
        return None
