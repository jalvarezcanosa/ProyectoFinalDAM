import uuid

from django.conf import settings
from django.utils import timezone

from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    telephone = models.CharField(max_length=12, unique=True)
    email = models.EmailField(max_length=254, unique=True)

class Counter(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='counter_images/', null=True, blank=True)

    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_counters')

    invite_code = models.UUIDField(default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField()
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, through='CounterMembership', related_name='counters')

    @property
    def is_open(self):
        return self.closed_at > timezone.now()

    @property
    def status(self):
        return 'open' if self.is_open else 'closed'

    def __str__(self):
        return self.title

class CounterMembership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    counter = models.ForeignKey(Counter, on_delete=models.CASCADE)
    individual_count = models.IntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Counter Entries'
        constraints = [
            models.UniqueConstraint(fields=['user', 'counter'], name='unique_user_counter_membership')
        ]