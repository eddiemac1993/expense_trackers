from django.contrib import admin

from .models import (
    ProjectRecord,
    ProjectExpense,
    ExpenseTag,
    PendingProjectRecord
)


class ProjectExpenseInline(admin.TabularInline):
    model = ProjectExpense
    extra = 0


@admin.register(ProjectRecord)
class ProjectRecordAdmin(admin.ModelAdmin):
    list_display = (
        "project_supply",
        "client",
        "contract_value",
        "paid_value",
        "status",
    )

    inlines = [ProjectExpenseInline]


admin.site.register(ProjectExpense)
admin.site.register(ExpenseTag)
admin.site.register(PendingProjectRecord)