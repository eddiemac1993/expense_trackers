from django.contrib import admin
from .models import ProjectRecord


@admin.register(ProjectRecord)
class ProjectRecordAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'company',
        'customer',
        'amount',
        'project_date',
        'status',
        'completion_status',
        'is_active',
    )

    list_filter = (
        'company',
        'status',
        'completion_status',
        'project_date',
        'year',
        'is_active',
    )

    search_fields = (
        'title',
        'company',
        'customer',
        'description',
    )

    ordering = ('-project_date',)

    list_editable = (
        'completion_status',
        'is_active',
    )

    readonly_fields = (
        'created_at',
        'year',
    )

    fieldsets = (
        ('Project Information', {
            'fields': (
                'title',
                'description',
                'company',
                'customer',
                'amount',
                'project_date',
                'year',
            )
        }),
        ('Status & Evaluation', {
            'fields': (
                'status',
                'completion_status',
                'is_active',
            )
        }),
        ('System', {
            'fields': ('created_at',),
        }),
    )
