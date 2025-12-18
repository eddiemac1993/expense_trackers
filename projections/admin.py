from django.contrib import admin
from .models import ProjectRecord

@admin.register(ProjectRecord)
class ProjectRecordAdmin(admin.ModelAdmin):
    list_display = ('company', 'customer', 'amount', 'project_date', 'status')
    list_filter = ('company', 'status', 'project_date')
    search_fields = ('company', 'customer')
