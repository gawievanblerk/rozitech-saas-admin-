"""
Notification models for messaging system
"""
from django.db import models


class Notification(models.Model):
    """
    Basic notification model - to be expanded
    """
    pass

    class Meta:
        db_table = 'notifications_notification'