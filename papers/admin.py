from django.contrib import admin
from .models import Company, Client, PaperEntry, PaperItem


class PaperItemInline(admin.TabularInline):
    model = PaperItem
    extra = 1


@admin.register(PaperEntry)
class PaperEntryAdmin(admin.ModelAdmin):
    inlines = [PaperItemInline]
    list_display = ('paper_number', 'company', 'client', 'total', 'date')


admin.site.register(Company)
admin.site.register(Client)