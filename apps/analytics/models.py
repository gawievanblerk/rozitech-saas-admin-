"""
Analytics models for tracking usage and metrics
"""
from django.db import models


class AnalyticsEvent(models.Model):
    """
    Basic analytics event model - to be expanded
    """
    pass

    class Meta:
        db_table = 'analytics_event'