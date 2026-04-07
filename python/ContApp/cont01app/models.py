import uuid

from django.contrib.auth.models import User
from django.db import models

# Create your models here.
class CounterGroup(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='counter_images/', null=True, blank=True)

    creator = models.ForeignKey(User, on_delete=models.CASCADE)

    invite_code = models.UUIDField(default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    close_at = models.DateTimeField()

    participants = models.ManyToManyField(User, related_name='counter_group_participants')

    def __str__(self):
        return self.title

class CountEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(CounterGroup, on_delete=models.CASCADE, related_name='entries')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Counter Entries'

    def __str__(self):
        return f'{self.user.username} +1 in {self.group.title}'



