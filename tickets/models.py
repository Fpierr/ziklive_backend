from django.db import models
from events.models import Event
from users.models import User
from django.utils import timezone
from django.contrib.auth import get_user_model


class TicketType(models.Model):
    """Un type de ticket mis en vente par un promoteur pour un événement"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="ticket_types")
    name = models.CharField(max_length=50)  # Ex: Standard, VIP
    price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField()
    sale_starts = models.DateTimeField()
    sale_ends = models.DateTimeField()
    created_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='ticket_types', null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.event.title}"

    @property
    def tickets_sold(self):
        return self.tickets.count()

    @property
    def tickets_remaining(self):
        return self.quantity - self.tickets_sold


class Ticket(models.Model):
    """Un ticket acheté par un fan pour un type donné"""
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE, related_name="tickets", null=True)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'fan'})
    purchased_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.ticket_type.name} - {self.buyer.name}"
