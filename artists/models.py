import string
import random
from django.db import models
from users.models import User
from django.utils import timezone
from datetime import timedelta
from cloudinary.models import CloudinaryField


class ArtistProfile(models.Model):
    name = models.CharField(max_length=255, unique=True, default="Unknown")
    email = models.EmailField(unique=True, blank=True, null=True)
    bio = models.TextField(blank=True)
    profile_image = CloudinaryField(
        'profile_image',
        folder='artists/profiles',
        blank=True,
        null=True,
        transformation=[],
    )
    user = models.OneToOneField(  # optional
        User, null=True, blank=True, on_delete=models.SET_NULL,
        limit_choices_to={'role': 'artist'}
    )
    created_at = models.DateTimeField(default=timezone.now)

    verification_code = models.CharField(max_length=20, blank=True, null=True)
    verification_code_expiry = models.DateTimeField(blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    STATUS_CHOICES = [
        ("invited", "Invited"),
        ("active", "Active"),
    ]
    status = models.CharField(max_length=20,
                              choices=STATUS_CHOICES,
                              default="invited")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'promoter'},
        related_name='created_artists'
    )

    def is_managed_by(self, promoter):
        return self.managers.filter(promoter=promoter, end_date__isnull=True).exists()

    def __str__(self):
        return self.name

    def generate_verification_code(self, length=12):
        chars = string.ascii_letters + string.digits
        self.verification_code = ''.join(random.choice(chars) for _ in range(length))
        self.verification_code_expiry = timezone.now() + timedelta(days=30)
        self.save()


class ArtistManager(models.Model):
    artist = models.ForeignKey(ArtistProfile, on_delete=models.CASCADE, related_name='managers')
    promoter = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'promoter'})
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(blank=True, null=True)

    class Meta:
        unique_together = ('artist', 'promoter')

    def __str__(self):
        return f"{self.promoter.name} manages {self.artist.name}"
