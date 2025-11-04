from django.contrib import admin
from .models import TicketType, Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_type', 'buyer', 'purchased_at', 'event_title')
    search_fields = ('ticket_type__name', 'buyer__name')
    list_filter = ('purchased_at', 'ticket_type__event')

    def event_title(self, obj):
        return obj.ticket_type.event.title
    event_title.short_description = "Event"


@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'price', 'quantity', 'tickets_sold', 'tickets_remaining')
    list_filter = ('event',)
    autocomplete_fields = ['event']

