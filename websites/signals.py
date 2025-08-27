from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify

from restaurants.models import Restaurant
from .models import Website


def _unique_slug(base: str) -> str:
    cand = slugify(base or "")[:120] or "site"
    slug = cand
    i = 1
    while Website.objects.filter(slug=slug).exists():
        i += 1
        slug = f"{cand}-{i}"
    return slug


@receiver(post_save, sender=Restaurant)
def ensure_single_website(sender, instance: Restaurant, created, **kwargs):
   
    qs = Website.objects.filter(restaurant=instance).order_by("id")

    if qs.exists():
        site = qs.first()
        qs.exclude(pk=site.pk).delete()
    else:
        base = instance.name or f"site-{instance.pk}"
        site = Website.objects.create(
            restaurant=instance,
            slug=_unique_slug(base),
            theme="default",
        )

    if not site.slug:
        base = instance.name or f"site-{instance.pk}"
        site.slug = _unique_slug(base)
        site.save(update_fields=["slug"])
