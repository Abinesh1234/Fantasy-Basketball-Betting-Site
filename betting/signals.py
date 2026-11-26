from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Transaction, UserProfile

STARTING_BALANCE = 1000


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        Transaction.objects.create(user=instance, amount=STARTING_BALANCE, reason="Starting balance")