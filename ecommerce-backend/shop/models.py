from django.db import models

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]
        verbose_name = 'category'
        verbose_name_plural = 'categories'
        
        def __str__(self):
            return self.verbose_name
        
class Product(models.Model):
    category = models.ForeignKey(
        Category,
        related_name='products',
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='products/%Y/%m/%d', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    
    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['id', 'name']),
            models.Index(fields=['slug']),
            models.Index(fields=['-created'])
        ]
        
    
    def __str__(self):
        return self.name