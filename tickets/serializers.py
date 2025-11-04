#!/usr/bin/env python3
"""tickets serializers"""


from rest_framework import serializers
from .models import Ticket, TicketType

class TicketTypeSerializer(serializers.ModelSerializer):
    tickets_sold = serializers.IntegerField(read_only=True)
    tickets_remaining = serializers.IntegerField(read_only=True)

    class Meta:
        model = TicketType
        fields = ['id', 'event', 'name', 'price', 'quantity', 'sale_starts', 'sale_ends', 'tickets_sold', 'tickets_remaining']


class TicketSerializer(serializers.ModelSerializer):
    ticket_type_name = serializers.CharField(source='ticket_type.name', read_only=True)
    event_title = serializers.CharField(source='ticket_type.event.title', read_only=True)

    class Meta:
        model = Ticket
        fields = ['id', 'ticket_type', 'ticket_type_name', 'event_title', 'buyer', 'purchased_at']
        read_only_fields = ['id', 'buyer', 'purchased_at']

