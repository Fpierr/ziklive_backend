#!/usr/bin/env python3
"""Streaming model to manage live creation"""

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid


class LiveStream(models.Model):
    """
    Model representing a live streaming session.
    Only users with 'promoter' or 'artist' roles can create streams.
    """

    STATUS_CHOICES = [
        ('idle', 'Idle'),
        ('live', 'Live'),
        ('ended', 'Ended'),
    ]

    STREAM_MODE_CHOICES = [
        ('obs', 'OBS/RTMP'),
        ('webcam', 'WebRTC (Browser)'),
    ]

    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_streams',
        limit_choices_to={'role__in': ['artist', 'promoter']},
        help_text="Artist or Promoter who created this stream"
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    stream_mode = models.CharField(
        max_length=10, 
        choices=STREAM_MODE_CHOICES, 
        default='obs'
    )
    stream_key = models.CharField(
        max_length=100, 
        unique=True, 
        editable=False,
        db_index=True
    )

    # OBS/RTMP configuration
    channel_arn = models.CharField(max_length=255, blank=True)
    playback_url = models.URLField(blank=True)
    ingest_endpoint = models.URLField(blank=True)

    # WebRTC configuration
    webrtc_session_id = models.CharField(max_length=100, blank=True)
    webrtc_offer = models.TextField(blank=True, help_text="SDP offer for WebRTC")
    webrtc_answer = models.TextField(blank=True, help_text="SDP answer for WebRTC")

    # Stream status and metrics
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='idle',
        db_index=True
    )
    viewer_count = models.PositiveIntegerField(default=0)
    peak_viewers = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    # Monetization
    is_paid = models.BooleanField(default=False)
    ticket_price = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0.00,
        help_text="Price in dollars"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Live Stream'
        verbose_name_plural = 'Live Streams'
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['created_by', '-created_at']),
            models.Index(fields=['stream_mode']),
        ]

    def __str__(self):
        live_creator = getattr(self.created_by, 'name', self.created_by.email)
        return f"{self.title} - {live_creator} ({self.get_status_display()}) ({self.get_stream_mode_display()})"

    def clean(self):
        """Validate model data before saving"""
        super().clean()

        # Validate creator role
        if self.created_by and self.created_by.role not in ['artist', 'promoter']:
            raise ValidationError({
                'created_by': 'Only users with Artist or Promoter role can create streams.'
            })

        # Validate paid stream
        if self.is_paid and self.ticket_price <= 0:
            raise ValidationError({
                'ticket_price': 'Paid streams must have a ticket price greater than 0.'
            })

        if self.stream_mode == 'obs' and self.status == 'live':
            if not self.ingest_endpoint or not self.playback_url:
                raise ValidationError(
                    'OBS streams require ingest_endpoint and playback_url.'
                )

        if self.stream_mode == 'webcam' and self.status == 'live':
            if not self.webrtc_session_id:
                raise ValidationError(
                    'WebRTC streams require a webrtc_session_id.'
                )

    def save(self, *args, **kwargs):
        # Generate unique stream key if not present
        if not self.stream_key:
            self.stream_key = str(uuid.uuid4())

        # Run validation
        self.full_clean()

        super().save(*args, **kwargs)

    # Stream lifecycle methods
    def go_live(self):
        """Transition stream to live status"""
        if self.status == 'live':
            return  # Already live

        self.status = 'live'
        self.started_at = timezone.now()
        self.viewer_count = 0
        self.save(update_fields=['status', 'started_at', 'viewer_count'])

    def end_stream(self):
        """End the stream and finalize metrics"""
        if self.status == 'ended':
            return  # Already ended
        
        self.status = 'ended'
        self.ended_at = timezone.now()
        self.viewer_count = 0
        self.save(update_fields=['status', 'ended_at', 'viewer_count'])

    # Viewer management methods
    def increment_viewers(self, count=1):
        """
        Increment viewer count atomically.
        Updates peak_viewers if current count exceeds it.
        """
        self.viewer_count += count
        
        if self.viewer_count > self.peak_viewers:
            self.peak_viewers = self.viewer_count
            self.save(update_fields=['viewer_count', 'peak_viewers'])
        else:
            self.save(update_fields=['viewer_count'])

    def decrement_viewers(self, count=1):
        """Decrement viewer count, ensuring it never goes below zero"""
        self.viewer_count = max(0, self.viewer_count - count)
        self.save(update_fields=['viewer_count'])

    def update_peak_viewers(self, value):
        """Update peak viewers if the provided value is higher"""
        if value > self.peak_viewers:
            self.peak_viewers = value
            self.save(update_fields=['peak_viewers'])

    # Utility properties
    @property
    def duration(self):
        """Calculate stream duration if applicable"""
        if not self.started_at:
            return None

        end_time = self.ended_at or timezone.now()
        return end_time - self.started_at

    @property
    def is_live(self):
        """Check if stream is currently live"""
        return self.status == 'live'

    @property
    def is_free(self):
        """Check if stream is free to watch"""
        return not self.is_paid


class StreamViewer(models.Model):
    """
    Track individual viewer sessions for analytics and billing.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    stream = models.ForeignKey(
        LiveStream, 
        on_delete=models.CASCADE, 
        related_name='views'
    )

    viewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='stream_views'
    )

    # Session tracking
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    # Timing
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Stream View'
        verbose_name_plural = 'Stream Views'
        indexes = [
            models.Index(fields=['stream', '-joined_at']),
            models.Index(fields=['viewer', '-joined_at']),
            models.Index(fields=['session_id']),
        ]

    def __str__(self):
        viewer_name = self.viewer.name if self.viewer else 'Anonymous'
        return f"{viewer_name} - {self.stream.title} ({self.duration_seconds}s)"

    def mark_left(self):
        """Mark viewer as left and calculate total duration"""
        if self.left_at:
            return  # Already marked as left
        
        self.left_at = timezone.now()
        self.duration_seconds = int((self.left_at - self.joined_at).total_seconds())
        self.save(update_fields=['left_at', 'duration_seconds'])

    @property
    def is_active(self):
        """Check if viewer is still watching"""
        return self.left_at is None
