from django.contrib import admin
from .models import Category, Document


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'uploaded_by',
        'uploaded_at',
        'expiry_date',
        'is_active',
    )
    list_filter = ('category', 'is_active')
    search_fields = ('title', 'description')
    date_hierarchy = 'uploaded_at'
