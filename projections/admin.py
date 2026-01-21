from django.contrib import admin
from django.db.models import Sum
from django.forms import ValidationError

from .models import ProjectRecord, Payment


# =========================
# PAYMENT INLINE (ADD PAYMENTS INSIDE PROJECT)
# =========================
class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1
    fields = (
        "amount_paid",
        "payment_date",
        "reference",
        "notes",
    )
    ordering = ("-payment_date",)


# =========================
# PROJECT ADMIN (UPDATED)
# =========================
@admin.register(ProjectRecord)
class ProjectRecordAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'company',
        'customer',
        'amount',
        'total_paid_display',
        'balance_due_display',
        'payment_status_display',
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
        'total_paid_display',
        'balance_due_display',
        'payment_status_display',
    )

    inlines = [PaymentInline]

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
        ('Payment Summary', {
            'fields': (
                'total_paid_display',
                'balance_due_display',
                'payment_status_display',
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

    # =========================
    # CALCULATED DISPLAY FIELDS
    # =========================
    def total_paid_display(self, obj):
        total = (
            obj.payments.aggregate(total=Sum("amount_paid"))
            .get("total") or 0
        )
        return f"ZMW {total:,.2f}"

    total_paid_display.short_description = "Total Paid"

    def balance_due_display(self, obj):
        total_paid = (
            obj.payments.aggregate(total=Sum("amount_paid"))
            .get("total") or 0
        )
        balance = obj.amount - total_paid
        return f"ZMW {balance:,.2f}"

    balance_due_display.short_description = "Balance Due"

    def payment_status_display(self, obj):
        total_paid = (
            obj.payments.aggregate(total=Sum("amount_paid"))
            .get("total") or 0
        )

        if total_paid == 0:
            return "UNPAID"
        elif total_paid < obj.amount:
            return "PARTIALLY PAID"
        return "PAID"

    payment_status_display.short_description = "Payment Status"


# =========================
# PAYMENT ADMIN (OPTIONAL STANDALONE VIEW)
# =========================
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "amount_paid",
        "payment_date",
        "reference",
    )

    list_filter = (
        "payment_date",
        "project__company",
    )

    search_fields = (
        "project__title",
        "reference",
    )

    ordering = ("-payment_date",)

    # =========================
    # OVERPAYMENT PROTECTION
    # =========================
    def save_model(self, request, obj, form, change):
        existing_total = (
            Payment.objects
            .filter(project=obj.project)
            .exclude(pk=obj.pk)
            .aggregate(total=Sum("amount_paid"))
            .get("total") or 0
        )

        if existing_total + obj.amount_paid > obj.project.amount:
            raise ValidationError(
                "Payment exceeds the project total amount."
            )

        super().save_model(request, obj, form, change)
