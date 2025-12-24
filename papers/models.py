from django.db import models
from django.utils.timezone import now


class Company(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to='logos/')
    address = models.TextField()
    phone = models.CharField(max_length=50)
    email = models.EmailField()

    def __str__(self):
        return self.name


class Client(models.Model):
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name


class PaperEntry(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    paper_number = models.CharField(max_length=50, unique=True, blank=True)
    date = models.DateField(default=now)

    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    prepared_by = models.CharField(max_length=255, blank=True)
    delivered_by = models.CharField(max_length=255, blank=True)
    received_by = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.paper_number

    def calculate_totals(self):
        self.subtotal = sum(item.amount for item in self.items.all())

        if self.tax_percentage > 0:
            self.tax_amount = (self.tax_percentage / 100) * self.subtotal
        else:
            self.tax_amount = 0

        self.total = self.subtotal + self.tax_amount


class PaperItem(models.Model):
    entry = models.ForeignKey(
        PaperEntry,
        related_name='items',
        on_delete=models.CASCADE
    )
    description = models.TextField()
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True)

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)
