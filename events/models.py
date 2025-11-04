from django.conf import settings
from django.db import models
from artists.models import ArtistProfile
from cloudinary.models import CloudinaryField
from django.utils import timezone
from django.core.exceptions import ValidationError


class Event(models.Model):
    artist = models.ForeignKey(ArtistProfile, on_delete=models.CASCADE,
                               related_name='events')
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    date = models.DateTimeField()
    banner = CloudinaryField(
        'banner',
        folder='events/banners',
        blank=True,
        null=True,
        transformation=[],
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_events',
        limit_choices_to={'role': ['promoter', 'admin']}
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    def clean(self):
        """Validate business logic"""
        super().clean()

        if self.date and self.date < timezone.now():
            raise ValidationError({
                'date': 'Event date must be in the future.'
            })

    @property
    def is_upcoming(self):
        """Check if event is in the future"""
        return self.date > timezone.now()

    @property
    def is_past(self):
        """Check if event has already occurred"""
        return self.date < timezone.now()

    @property
    def days_until(self):
        """Calculate days until event"""
        if self.is_past:
            return None
        delta = self.date - timezone.now()
        return delta.days