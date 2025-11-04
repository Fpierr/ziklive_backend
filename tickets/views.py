from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Ticket, TicketType
from .serializers import TicketSerializer, TicketTypeSerializer
from .permissions import IsFan, IsPromoterOrAdmin
from rest_framework.exceptions import PermissionDenied


class TicketPurchaseViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated, IsFan]

    def get_queryset(self):
        return Ticket.objects.filter(buyer=self.request.user)

    def perform_create(self, serializer):
        ticket_type = serializer.validated_data['ticket_type']
        now = timezone.now()

        # Conditions de vente
        if not (ticket_type.sale_starts <= now <= ticket_type.sale_ends):
            raise serializer.ValidationError("Sale close for this ticket.")
        if ticket_type.tickets_remaining <= 0:
            raise serializer.ValidationError("Ce ticket est épuisé.")

        serializer.save(buyer=self.request.user)


class TicketTypeViewSet(viewsets.ModelViewSet):
    queryset = TicketType.objects.all()
    serializer_class = TicketTypeSerializer
    permission_classes = [IsAuthenticated, IsPromoterOrAdmin]

    def get_queryset(self):
        # Un promoteur ne voit que ses propres ticket types
        queryset = TicketType.objects.filter(event__created_by=self.request.user)
        event_id = self.request.query_params.get('event')
        if event_id:
            queryset = queryset.filter(event__id=event_id)
        return queryset

    def perform_create(self, serializer):
        if self.request.user.role not in ['promoter', 'admin']:
            raise PermissionDenied("Only promoter can create events.")
        serializer.save(created_by=self.request.user)


class SoldTicketsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated, IsPromoterOrAdmin]

    def get_queryset(self):
        user = self.request.user
        # Tickets vendus pour les ticket types des événements de ce promoteur
        return Ticket.objects.filter(ticket_type__event__created_by=user)
