from django.db import models

# Create your models here.
class User(models.Model):
    username = models.CharField(max_length=20)
    password = models.CharField(max_length=20)

class Counters(models.Model):
    counter_name = models.CharField(max_length=100)
    counter_title = models.CharField(max_length=250)
    counter_img = models.ImageField(upload_to='counter_img')


