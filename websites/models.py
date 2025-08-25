from django.db import models
from django.utils.text import slugify
from restaurants.models import Restaurant

class Website(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="websites")
    theme = models.CharField(max_length=100, default="default")
    custom_colors = models.CharField(max_length=255, blank=True, null=True)
    secondary_color = models.CharField(max_length=255, blank=True, null=True)
    logo = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(max_length=140, unique=True, null=True, blank=True)
    subdomain = models.CharField(max_length=63, blank=True, null=True)           
    domain = models.CharField(max_length=255, blank=True, null=True)            

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = getattr(self.restaurant, "name", None) or f"site-{self.pk or ''}"
            self.slug = slugify(base)[:140] or None
        super().save(*args, **kwargs)
