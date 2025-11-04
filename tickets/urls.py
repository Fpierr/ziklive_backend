# tickets/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SoldTicketsViewSet, TicketPurchaseViewSet, TicketTypeViewSet

router = DefaultRouter()
router.register(r'my-tickets', TicketPurchaseViewSet, basename='my-tickets')
router.register(r'manage-types', TicketTypeViewSet, basename='ticket-types')
router.register(r'sold-tickets', SoldTicketsViewSet, basename='sold-tickets')

urlpatterns = [
    path('', include(router.urls)),
]
