from django.contrib import admin
from .models import ArtistProfile, ArtistManager

@admin.register(ArtistProfile)
class ArtistProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'status', 'email_verified', 'created_by')
    list_filter = ('status', 'email_verified', 'created_by')
    search_fields = ('name', 'email')
    readonly_fields = ('created_at', 'verification_code', 'verification_code_expiry')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('created_by')


@admin.register(ArtistManager)
class ArtistManagerAdmin(admin.ModelAdmin):
    list_display = ('promoter', 'artist', 'start_date', 'end_date')
    list_filter = ('promoter',)
    search_fields = ('artist__name', 'promoter__name')

    def artist_email(self, obj):
        return obj.artist.email
    artist_email.short_description = "Artist Email"
