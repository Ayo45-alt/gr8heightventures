from django.db import models


class DailyPageView(models.Model):
    day = models.DateField(unique=True)
    views = models.PositiveBigIntegerField(default=0)

    class Meta:
        ordering = ['-day']
        verbose_name = 'daily page view'
        verbose_name_plural = 'daily page views'

    def __str__(self):
        return f'{self.day}: {self.views} page views'
