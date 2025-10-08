from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.name


class Tender(models.Model):
    tender_no = models.CharField(max_length=100, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="tenders")
    client_name = models.CharField(max_length=255)
    total_value = models.DecimalField(max_digits=12, decimal_places=2)
    payment_status = models.CharField(
        max_length=50,
        choices=[
            ("Pending", "Pending"),
            ("Partially Paid", "Partially Paid"),
            ("Paid", "Paid"),
        ],
        default="Pending"
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def total_expenses(self):
        return sum(e.amount for e in self.expenses.all())

    def profit(self):
        return self.total_value - self.total_expenses()

    def __str__(self):
        return f"{self.tender_no} - {self.company.name}"


class Expense(models.Model):
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, related_name="expenses")
    category = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.category} - {self.amount}"
