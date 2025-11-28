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
    total_value = models.DecimalField(max_digits=12, decimal_places=2)
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

    def profit(self):
        return (self.total_value or Decimal('0.00')) - self.total_expenses()

    def __str__(self):
        return f"{self.tender_no} - {self.company.name}"

    def get_absolute_url(self):
        return reverse('tracker:tender_edit', args=[self.pk])


class Expense(models.Model):
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, related_name="expenses")
    category = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.category} - {self.amount}"

    def get_absolute_url(self):
        return reverse('tracker:expense_edit', args=[self.pk])
