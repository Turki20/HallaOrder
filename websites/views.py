from django.shortcuts import render, get_object_or_404
from .models import Website

def site_home(request, slug):
    website = get_object_or_404(Website, slug=slug)
    return render(request, "websites/base.html", {"website": website})

def preview(request, pk):
    website = get_object_or_404(Website, pk=pk)
    return render(request, "websites/base.html", {"website": website, "is_preview": True})
