from django.contrib import admin

from .models import (
    ExpenseTag,
    ProjectExpense,
    ProjectRecord,
)


class ProjectExpenseInline(admin.TabularInline):
    model = ProjectExpense
    extra = 1

    fields = (
        "date",
        "reason",
        "tag",
        "amount",
        "notes",
    )


@admin.register(ProjectRecord)
class ProjectRecordAdmin(admin.ModelAdmin):
    list_display = (
        "company",
        "project_supply",
        "client",
        "start_date",
        "end_date",
        "contract_value",
        "tax_type",
        "tax_amount",
        "contract_excluding_tax",
        "expense_value",
        "profit_value",
        "paid_value",
        "pending_payment_value",
        "status",
    )

    list_filter = (
        "status",
        "tax_type",
        "company",
        "client",
        "start_date",
    )

    search_fields = (
        "company",
        "project_supply",
        "client",
    )

    readonly_fields = (
        "tax_rate",
        "tax_amount",
        "contract_excluding_tax",
        "expense_value",
        "profit_value",
        "pending_payment_value",
        "balance_value",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Project Details",
            {
                "fields": (
                    "company",
                    "project_supply",
                    "client",
                    "start_date",
                    "end_date",
                    "status",
                )
            },
        ),
        (
            "Financial Details",
            {
                "fields": (
                    "contract_value",
                    "tax_type",
                    "tax_rate",
                    "tax_amount",
                    "contract_excluding_tax",
                    "paid_value",
                    "pending_payment_value",
                    "expense_value",
                    "profit_value",
                    "balance_value",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    inlines = [ProjectExpenseInline]

    ordering = (
        "start_date",
        "created_at",
    )


@admin.register(ProjectExpense)
class ProjectExpenseAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "date",
        "reason",
        "tag",
        "amount",
        "created_at",
    )

    list_filter = (
        "tag",
        "date",
        "project__company",
    )

    search_fields = (
        "reason",
        "notes",
        "project__company",
        "project__project_supply",
        "project__client",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = (
        "-date",
        "-created_at",
    )


@admin.register(ExpenseTag)
class ExpenseTagAdmin(admin.ModelAdmin):
    list_display = (
        "name",
    )

    search_fields = (
        "name",
    )

    ordering = (
        "name",
    )