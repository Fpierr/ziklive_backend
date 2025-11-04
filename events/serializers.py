from rest_framework import serializers
from django.utils import timezone
from events.models import Event
from artists.models import ArtistProfile, ArtistManager

class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArtistProfile
        fields = ['id', 'name', 'profile_image']

class EventSerializer(serializers.ModelSerializer):
    artist = ArtistSerializer(read_only=True)
    artist_name = serializers.CharField(source='artist.name', read_only=True)
    is_upcoming = serializers.SerializerMethodField()
    is_past = serializers.SerializerMethodField()
    banner = serializers.ImageField(read_only=True)
    banner_url = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'artist_name', 'banner_url']

    def get_is_upcoming(self, obj):
        return obj.date >= timezone.now()

    def get_is_past(self, obj):
        return obj.date < timezone.now()
    
    def get_banner_url(self, obj):
        if obj.banner:
            return obj.banner.url
        return None


class EventCreateSerializer(serializers.ModelSerializer):
    artist_id = serializers.IntegerField(write_only=True)
    banner = serializers.ImageField(required=False)

    class Meta:
        model = Event
        fields = [
            'title', 'description', 'location', 'date', 'banner', 'artist_id'
        ]

    def validate_artist_id(self, value):
        try:
            return ArtistProfile.objects.get(id=value)
        except ArtistProfile.DoesNotExist:
            raise serializers.ValidationError('Unknown Artist for this ID.')

    def create(self, validated_data):
        artist = validated_data.pop('artist_id')
        user = self.context['request'].user
        validated_data['artist'] = artist
        validated_data['created_by'] = user

        if user.role == 'promoter':
            ArtistManager.objects.get_or_create(
                artist=artist,
                promoter=user,
                end_date__isnull=True
            )

        return super().create(validated_data)
