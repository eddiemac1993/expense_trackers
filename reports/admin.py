from django.contrib import admin
from .models import (
    ProjectRecord,
    ProjectExpense,
    ExpenseTag
)


class ProjectExpenseInline(admin.TabularInline):
    model = ProjectExpense
    extra = 1


@admin.register(ProjectRecord)
class ProjectRecordAdmin(admin.ModelAdmin):
    list_display = (
        "company",
        "project_supply",
        "client",
        "contract_value",
        "expense_value",
        "profit_value",
        "paid_value",
        "status",
    )

    search_fields = (
        "company",
        "project_supply",
        "client",
    )

    list_filter = (
        "status",
        "company",
    )

    inlines = [ProjectExpenseInline]


@admin.register(ProjectExpense)
class ProjectExpenseAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "date",
        "reason",
        "tag",
        "amount",
    )

    list_filter = (
        "tag",
        "date",
    )

    search_fields = (
        "reason",
        "project__project_supply",
    )


@admin.register(ExpenseTag)
class ExpenseTagAdmin(admin.ModelAdmin):
    list_display = ("name",)