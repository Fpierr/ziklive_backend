from rest_framework import viewsets
from events.models import Event
from events.serializers import EventCreateSerializer, EventSerializer
from users.permissions import IsAdminOrPromoter
from events.utils.mixins import OwnerRestrictedMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from django.utils import timezone


class EventViewSet(OwnerRestrictedMixin, viewsets.ModelViewSet):
    queryset = Event.objects.all().order_by('-date')
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated, IsAdminOrPromoter]
    owner_field = 'created_by'

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return EventCreateSerializer
        return EventSerializer


class PublicEventsListView(ListAPIView):
    queryset = Event.objects.filter(
        date__gte=timezone.now()).order_by('-date')

    serializer_class = EventSerializer
    permission_classes = [AllowAny]


class PastEventsListView(ListAPIView):
    queryset = Event.objects.filter(
        date__lt=timezone.now()).order_by('-date')

    serializer_class = EventSerializer
    permission_classes = [AllowAny]
