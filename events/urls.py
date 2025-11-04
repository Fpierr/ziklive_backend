from django.urls import path, include
from rest_framework.routers import DefaultRouter
from events.views import EventViewSet, PastEventsListView
from events.views import PublicEventsListView

router = DefaultRouter()
router.register(r'manage', EventViewSet, basename='event')

urlpatterns = [
    path('', include(router.urls)),
    path('public/', PublicEventsListView.as_view(),
         name='public-upcoming-events-list'),
    path('public/past/', PastEventsListView.as_view(),
         name='past-events-list'),
]
