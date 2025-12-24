from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.timezone import now
from .models import PaperEntry


@receiver(pre_save, sender=PaperEntry)
def generate_paper_number(sender, instance, **kwargs):
    if not instance.paper_number:
        year = now().year
        count = PaperEntry.objects.filter(company=instance.company).count() + 1
        instance.paper_number = f"{instance.company.slug.upper()}/{year}/{count:04d}"