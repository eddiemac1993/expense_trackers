from django.db import models


class ProjectRecord(models.Model):
    STATUS_CHOICES = (
        ('WON', 'Won'),
        ('LOST', 'Lost'),
        ('PENDING', 'Pending'),
    )

    COMPLETION_CHOICES = (
        ('PENDING_EVALUATION', 'Pending Evaluation'),
        ('NOT_COMPLETED', 'Not Completed'),
        ('COMPLETED', 'Completed'),
    )

    title = models.CharField(
        max_length=255,
        db_index=True,
        default="Untitled Project",
        help_text="Short project title"
    )

    description = models.TextField(
        blank=True,
        help_text="Detailed project description"
    )

    company = models.CharField(
        max_length=200,
        db_index=True
    )

    customer = models.CharField(
        max_length=200,
        db_index=True
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    project_date = models.DateField(
        db_index=True
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        db_index=True
    )

    completion_status = models.CharField(
        max_length=25,
        choices=COMPLETION_CHOICES,
        default='PENDING_EVALUATION',
        db_index=True,
        help_text="Project execution and evaluation status"
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True
    )

    year = models.PositiveIntegerField(
        editable=False,
        db_index=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-project_date']

    def save(self, *args, **kwargs):
        if self.project_date:
            self.year = self.project_date.year
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.title} | "
            f"{self.company} | "
            f"{self.get_completion_status_display()}"
        )
