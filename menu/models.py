# menu/models.py

from django.db import models
from restaurants.models import Restaurant
from django.core.validators import MinValueValidator

def get_product_image_path(instance, filename):
    return f'restaurants/{instance.product.category.restaurant.id}/products/{instance.product.id}/{filename}'

# --- NEW HELPER FOR MEAL IMAGES ---
def get_meal_image_path(instance, filename):
    return f'restaurants/{instance.restaurant.id}/meals/{instance.id}/{filename}'

class Category(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    position = models.PositiveIntegerField(default=0)
    class Meta:
        ordering = ['position']; verbose_name_plural = "Categories"
    def __str__(self): return f"{self.name} ({self.restaurant.name})"

class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    position = models.PositiveIntegerField(default=0)
    option_groups = models.ManyToManyField('OptionGroup', blank=True, related_name='products')
    class Meta: ordering = ['position']
    def __str__(self): return self.name
    @property
    def cover_image(self):
        cover = self.images.filter(is_cover=True).first()
        return cover.image if cover else (self.images.first().image if self.images.exists() else None)

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to=get_product_image_path)
    is_cover = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-is_cover', 'uploaded_at']
    def __str__(self): return f"Image for {self.product.name}"
    def save(self, *args, **kwargs):
        if self.is_cover: ProductImage.objects.filter(product=self.product).exclude(pk=self.pk).update(is_cover=False)
        elif not ProductImage.objects.filter(product=self.product).exclude(pk=self.pk).exists(): self.is_cover = True
        super().save(*args, **kwargs)
    def delete(self, *args, **kwargs):
        is_this_cover = self.is_cover; super().delete(*args, **kwargs)
        if is_this_cover:
            next_image = self.product.images.order_by('uploaded_at').first()
            if next_image: next_image.is_cover = True; next_image.save()

class OptionGroup(models.Model):
    class SelectionType(models.TextChoices):
        SINGLE = 'SINGLE', 'خيار واحد'; MULTIPLE = 'MULTIPLE', 'خيارات متعددة'
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='option_groups')
    name = models.CharField(max_length=100)
    selection_type = models.CharField(max_length=10, choices=SelectionType.choices, default=SelectionType.SINGLE)
    is_required = models.BooleanField(default=False)
    min_selection = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    max_selection = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    class Meta: ordering = ['name']; unique_together = ('restaurant', 'name')
    def __str__(self): return f"{self.name} ({self.restaurant.name})"

class Option(models.Model):
    group = models.ForeignKey(OptionGroup, on_delete=models.CASCADE, related_name='options')
    name = models.CharField(max_length=100)
    price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    position = models.PositiveIntegerField(default=0)
    class Meta: ordering = ['position', 'name']
    def __str__(self): return f"{self.name} (+{self.price_adjustment})"

# --- NEW MODELS FOR PHASE 3 ---

class Meal(models.Model):
    """Represents a bundled meal/combo deal."""
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='meals')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="The fixed price for the entire meal.")
    image = models.ImageField(upload_to=get_meal_image_path, blank=True, null=True)
    available = models.BooleanField(default=True)
    position = models.PositiveIntegerField(default=0)
    # Meals can also have their own options, e.g., "Choose your drink for the combo"
    option_groups = models.ManyToManyField('OptionGroup', blank=True, related_name='meals')
    
    class Meta:
        ordering = ['position', 'name']

    def __str__(self):
        return f"Meal: {self.name}"

class MealItem(models.Model):
    """An individual product included in a meal."""
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='meal_items')
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in {self.meal.name}"