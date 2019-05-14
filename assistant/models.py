import datetime
from django.db import models
from django.utils import timezone


class Info(models.Model):
    message           = models.CharField(max_length=200)
    message_timestamp = models.DateTimeField('date messaged', auto_now=True)

    def was_updated_recently(self):
        return self.message_timestamp >= timezone.now() - datetime.timedelta(hours=3)
