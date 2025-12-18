from django.db import models
from django.urls import reverse
from decimal import Decimal

class Company(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('tracker:company_edit', args=[self.pk])


class Tender(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Partially Paid", "Partially Paid"),
        ("Paid", "Paid"),
    ]

    tender_no = models.CharField(max_length=100, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="tenders")
    client_name = models.CharField(max_length=255)
    total_value = models.DecimalField(max_digits=14, decimal_places=2)
    payment_status = models.CharField(
        max_length=50,
        choices=PAYMENT_STATUS_CHOICES,
        default="Pending"
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-start_date']

    def total_expenses(self):
        total = self.expenses.aggregate(total=models.Sum('amount'))['total']
        return total or Decimal('0.00')

    def total_paid(self):
        """Sum of payments received for this tender"""
        total = self.payments.aggregate(total=models.Sum('amount'))['total']
        return total or Decimal('0.00')

    def balance(self):
        """Amount client still owes (could be 0)"""
        return (self.total_value or Decimal('0.00')) - self.total_paid()

    def profit(self):
        """Profit = tender value - expenses. This may be negative (loss)."""
        return (self.total_value or Decimal('0.00')) - self.total_expenses()

    def expense_overrun(self):
        """If expenses exceed tender value, return amount of overrun (positive), else 0"""
        over = self.total_expenses() - (self.total_value or Decimal('0.00'))
        return over if over > 0 else Decimal('0.00')

    def update_payment_status(self):
        paid = self.total_paid()
        if paid <= 0:
            self.payment_status = 'Pending'
        elif paid < self.total_value:
            self.payment_status = 'Partially Paid'
        else:
            self.payment_status = 'Paid'
        # do not save here to allow caller to control save

    def __str__(self):
        return f"{self.tender_no} - {self.company.name}"

    def get_absolute_url(self):
        return reverse('tracker:tender_edit', args=[self.pk])


class Expense(models.Model):
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, related_name="expenses")
    category = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    date = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.category} - {self.amount}"

    def get_absolute_url(self):
        return reverse('tracker:expense_edit', args=[self.pk])


class Payment(models.Model):
    """
    Records payments/receipts from the client for a tender.
    Allows partial payments and full payments to be tracked separately from expenses.
    """
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    note = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Payment {self.amount} for {self.tender.tender_no}"
