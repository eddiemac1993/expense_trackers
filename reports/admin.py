from django.contrib import admin

from .models import (
    ExpenseTag,
    PendingProjectRecord,
    ProjectExpense,
    ProjectPayment,
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
        "currency",
        "exchange_rate",
        "notes",
    )


class ProjectPaymentInline(admin.TabularInline):
    model = ProjectPayment
    extra = 1

    fields = (
        "date",
        "reference",
        "amount",
        "tax_rate",
        "currency",
        "exchange_rate",
        "tax_amount_zmw",
        "net_amount_zmw",
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
        "currency",
        "exchange_rate",
        "contract_value",
        "tax_type",
        "tax_amount",
        "contract_excluding_tax",
        "expense_value",
        "profit_value",
        "paid_value",
        "paid_value_zmw",
        "payment_value",
        "pending_payment_value",
        "status",
    )

    list_filter = (
        "status",
        "tax_type",
        "currency",
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
        "contract_value_zmw",
        "paid_value_zmw",
        "payment_value",
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
                    "currency",
                    "exchange_rate",
                    "contract_value_zmw",
                    "tax_type",
                    "tax_rate",
                    "tax_amount",
                    "contract_excluding_tax",
                    "paid_value",
                    "paid_value_zmw",
                    "payment_value",
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

    inlines = [ProjectExpenseInline, ProjectPaymentInline]

    ordering = (
        "start_date",
        "created_at",
    )


@admin.register(PendingProjectRecord)
class PendingProjectRecordAdmin(admin.ModelAdmin):
    list_display = (
        "company",
        "project_supply",
        "client",
        "submission_date",
        "expected_award_date",
        "currency",
        "exchange_rate",
        "contract_value",
        "tax_type",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "tax_type",
        "currency",
        "company",
        "client",
        "submission_date",
        "expected_award_date",
    )

    search_fields = (
        "company",
        "project_supply",
        "client",
        "notes",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Pending Project Details",
            {
                "fields": (
                    "company",
                    "project_supply",
                    "client",
                    "submission_date",
                    "expected_award_date",
                    "status",
                )
            },
        ),
        (
            "Financial Details",
            {
                "fields": (
                    "contract_value",
                    "currency",
                    "exchange_rate",
                    "tax_type",
                )
            },
        ),
        (
            "Notes",
            {
                "fields": (
                    "notes",
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

    ordering = (
        "submission_date",
        "created_at",
    )


@admin.register(ProjectExpense)
class ProjectExpenseAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "date",
        "reason",
        "tag",
        "currency",
        "exchange_rate",
        "amount",
        "amount_zmw",
        "created_at",
    )

    list_filter = (
        "tag",
        "currency",
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
        "amount_zmw",
        "created_at",
    )

    ordering = (
        "-date",
        "-created_at",
    )


@admin.register(ProjectPayment)
class ProjectPaymentAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "date",
        "reference",
        "currency",
        "exchange_rate",
        "amount",
        "tax_rate",
        "amount_zmw",
        "tax_amount_zmw",
        "net_amount_zmw",
        "created_at",
    )

    list_filter = (
        "currency",
        "date",
        "project__company",
    )

    search_fields = (
        "reference",
        "notes",
        "project__company",
        "project__project_supply",
        "project__client",
    )

    readonly_fields = (
        "amount_zmw",
        "tax_amount_zmw",
        "net_amount_zmw",
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
