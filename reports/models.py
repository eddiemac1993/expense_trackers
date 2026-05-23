from django.db import models


class ProjectRecord(models.Model):
    STATUS_CHOICES = [
        ("Not started", "Not started"),
        ("Started", "Started"),
        ("Partial Done", "Partial Done"),
        ("Done", "Done"),
    ]

    company = models.CharField(max_length=255)
    project_supply = models.CharField("Project / Supply", max_length=255)
    client = models.CharField(max_length=255)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    contract_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    paid_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="Not started"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def expense_value(self):
        return sum(expense.amount for expense in self.expenses.all())

    @property
    def profit_value(self):
        return self.contract_value - self.expense_value

    @property
    def balance_value(self):
        return self.contract_value - self.paid_value

    def __str__(self):
        return f"{self.company} - {self.project_supply}"


class ExpenseTag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class ProjectExpense(models.Model):
    project = models.ForeignKey(
        ProjectRecord,
        on_delete=models.CASCADE,
        related_name="expenses"
    )

    date = models.DateField()
    reason = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=15, decimal_places=2)

    tag = models.ForeignKey(
        ExpenseTag,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.project.project_supply} - ZMW {self.amount}"