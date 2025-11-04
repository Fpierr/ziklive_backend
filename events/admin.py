from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'location', 'date', 'created_by')
    list_filter = ('artist', 'created_by', 'date')
    search_fields = ('title', 'location', 'artist__name')
    autocomplete_fields = ['artist', 'created_by']
