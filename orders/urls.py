from django.urls import path
from . import views

app_name = "orders"  

urlpatterns = [
    path("board/", views.order_board_default, name="order_board"),                   # no param
    path("board/<int:branch_id>/", views.order_board, name="order_board_by_branch"),# with param
    path("<int:pk>/advance/", views.advance_status, name="order_advance"),
    path("<int:pk>/cancel/", views.cancel_order, name="order_cancel"),
    path("<int:pk>/fragment/", views.order_detail_fragment, name="order_detail_fragment"),
]