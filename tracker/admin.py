from django.contrib import admin
from django.db.models import Sum
from django.utils.html import format_html
from .models import Company, Tender, Expense


class ExpenseInline(admin.TabularInline):
    """Inline editing for expenses within Tender admin"""
    model = Expense
    extra = 1
    fields = ('category', 'description', 'amount', 'date')
    readonly_fields = ('date',)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'tender_count', 'total_tender_value')
    list_filter = ('name',)
    search_fields = ('name', 'address', 'email')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Address Information', {
            'fields': ('address',),
            'classes': ('collapse',)
        }),
    )
    
    def tender_count(self, obj):
        return obj.tenders.count()
    tender_count.short_description = 'Total Tenders'
    
    def total_tender_value(self, obj):
        total = obj.tenders.aggregate(total=Sum('total_value'))['total'] or 0
        return f"${total:,.2f}"
    total_tender_value.short_description = 'Total Tender Value'


@admin.register(Tender)
class TenderAdmin(admin.ModelAdmin):
    list_display = (
        'tender_no', 
        'company', 
        'client_name', 
        'total_value_formatted',
        'total_expenses_display',
        'profit_display',
        'payment_status_colored',
        'start_date',
        'end_date',
        'duration_days'
    )
    
    list_filter = (
        'payment_status',
        'company',
        'start_date',
        'end_date'
    )
    
    search_fields = (
        'tender_no',
        'client_name',
        'company__name'
    )
    
    readonly_fields = (
        'total_expenses_display',
        'profit_display',
        'profit_margin'
    )
    
    fieldsets = (
        ('Tender Information', {
            'fields': (
                'tender_no',
                'company',
                'client_name',
                'total_value'
            )
        }),
        ('Dates & Status', {
            'fields': (
                'start_date',
                'end_date',
                'payment_status'
            )
        }),
        ('Financial Summary', {
            'fields': (
                'total_expenses_display',
                'profit_display',
                'profit_margin'
            ),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ExpenseInline]
    
    # Custom methods for display
    def total_value_formatted(self, obj):
        return f"${obj.total_value:,.2f}"
    total_value_formatted.short_description = 'Total Value'
    total_value_formatted.admin_order_field = 'total_value'
    
    def total_expenses_display(self, obj):
        expenses = obj.total_expenses()
        return f"${expenses:,.2f}"
    total_expenses_display.short_description = 'Total Expenses'
    
    def profit_display(self, obj):
        profit = obj.profit()
        color = 'green' if profit >= 0 else 'red'
        # Use string formatting before passing to format_html
        profit_str = f"${profit:,.2f}"
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            profit_str
        )
    profit_display.short_description = 'Profit/Loss'
    
    def profit_margin(self, obj):
        if obj.total_value > 0:
            margin = (obj.profit() / obj.total_value) * 100
            color = 'green' if margin >= 0 else 'red'
            # Use string formatting before passing to format_html
            margin_str = f"{margin:,.1f}%"
            return format_html(
                '<span style="color: {};">{}</span>',
                color,
                margin_str
            )
        return "N/A"
    profit_margin.short_description = 'Profit Margin'
    
    def payment_status_colored(self, obj):
        color_map = {
            'Pending': 'orange',
            'Partially Paid': 'blue',
            'Paid': 'green'
        }
        color = color_map.get(obj.payment_status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.payment_status  # This is a regular string, not formatted
        )
    payment_status_colored.short_description = 'Payment Status'
    
    def duration_days(self, obj):
        if obj.start_date and obj.end_date:
            duration = (obj.end_date - obj.start_date).days
            return f"{duration} days"
        return "N/A"
    duration_days.short_description = 'Duration'


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        'tender',
        'category',
        'description_short',
        'amount_formatted',
        'date'
    )
    
    list_filter = (
        'category',
        'date',
        'tender__company'
    )
    
    search_fields = (
        'category',
        'description',
        'tender__tender_no',
        'tender__client_name'
    )
    
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Expense Details', {
            'fields': (
                'tender',
                'category',
                'description',
                'amount',
                'date'
            )
        }),
    )
    
    # Custom methods
    def amount_formatted(self, obj):
        return f"${obj.amount:,.2f}"
    amount_formatted.short_description = 'Amount'
    amount_formatted.admin_order_field = 'amount'
    
    def description_short(self, obj):
        if obj.description:
            return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
        return "-"
    description_short.short_description = 'Description'


# Admin site customization
admin.site.site_header = 'Expense Tracker Administration'
admin.site.site_title = 'Expense Tracker Admin'
admin.site.index_title = 'Welcome to Expense Tracker Admin'