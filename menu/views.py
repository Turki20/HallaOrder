from django.shortcuts import render
from django.http import HttpRequest, HttpResponse


def menu_view(request: HttpRequest) -> HttpResponse:    
    return render(request, 'menu/menu.html')