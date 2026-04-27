import uuid
from django.utils import timezone

from django.contrib.auth.models import User
from django.db import models

# Create your models here.
class Counter(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='counter_images/', null=True, blank=True)

    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_counters')

    invite_code = models.UUIDField(default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField()

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed')
    ]

    status = models.CharField(choices=STATUS_CHOICES, max_length=10, default='open')
    participants = models.ManyToManyField(User, through='CounterMembership', related_name='counters')
    def __str__(self):
        return self.title

class CounterMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    counter = models.ForeignKey(Counter, on_delete=models.CASCADE)
    individual_count = models.IntegerField(default=0)
    joined_at = models.DateTimeField(auto_now=timezone.now())

    class Meta:
        verbose_name_plural = 'Counter Entries'
        unique_together = ('user', 'counter')