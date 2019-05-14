import datetime
from django.db import models
from django.utils import timezone


class Info(models.Model):
    message = models.CharField(max_length=1000)
    message_timestamp = models.DateTimeField('date messaged', auto_now=True)

    def was_updated_recently(self):
        return self.message_timestamp >= timezone.now() - datetime.timedelta(hours=3)

    def __str__(self):
        return self.message[:50]


class QuickMessage(models.Model):
    message = models.CharField(max_length=1000)

    def __str__(self):
        return self.message[:50]
