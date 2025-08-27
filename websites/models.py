from django.db import models
from django.utils.text import slugify
from django.conf import settings
from restaurants.models import Restaurant

class Website(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="websites")
    theme = models.CharField(max_length=100, default="default")
    custom_colors = models.CharField(max_length=255, blank=True, null=True)   # primary
    secondary_color = models.CharField(max_length=255, blank=True, null=True) # accent
    logo = models.ImageField(upload_to="logos/", blank=True, null=True)

    slug = models.SlugField(max_length=140, unique=True, blank=True, default="")

    subdomain = models.CharField(max_length=63, blank=True, null=True)
    domain = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def display_name(self):
        return getattr(self.restaurant, "name", "") or "متجري"

    @property
    def logo_url(self) -> str:
        if self.logo:
            try:
                return self.logo.url
            except Exception:
                pass
        raw = getattr(self, "logo", "") or ""
        if isinstance(raw, str) and raw:
            if raw.startswith("http") or raw.startswith("/"):
                return raw
            return f"{settings.MEDIA_URL}{raw}"
        return ""

    def save(self, *args, **kwargs):
        if not self.slug:
            base = (getattr(self.restaurant, "name", None) or f"site-{self.pk or ''}").strip()
            cand = slugify(base)[:120] or "site"
            slug = cand
            i = 1
            from .models import Website as W  
            while W.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{cand}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.display_name} · {self.slug}"
