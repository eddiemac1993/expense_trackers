from django.contrib import admin
from .models import Company, CompanyBankAccount, Client, PaperEntry, PaperItem


class CompanyBankAccountInline(admin.TabularInline):
    model = CompanyBankAccount
    extra = 1


class PaperItemInline(admin.TabularInline):
    model = PaperItem
    extra = 1


@admin.register(PaperEntry)
class PaperEntryAdmin(admin.ModelAdmin):
    inlines = [PaperItemInline]
    list_display = ('paper_number', 'company', 'bank_account', 'client', 'total', 'date')


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    inlines = [CompanyBankAccountInline]
    list_display = ("name", "slug", "phone", "email")
    search_fields = ("name", "slug")


@admin.register(CompanyBankAccount)
class CompanyBankAccountAdmin(admin.ModelAdmin):
    list_display = (
        "company",
        "display_label",
        "bank_name",
        "account_number",
        "account_number_usd",
        "is_default",
    )
    list_filter = ("company", "bank_name", "is_default")
    search_fields = (
        "company__name",
        "bank_name",
        "account_name",
        "account_number",
        "account_number_usd",
    )


admin.site.register(Client)
