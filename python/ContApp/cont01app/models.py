from django.db import models

# Create your models here.
class CounterGroup(models.Model):
    titulo = models.CharField(max_length=100)
    description = models.TextField(blank=True)

