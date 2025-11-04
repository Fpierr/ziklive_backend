from rest_framework import serializers
from artists.models import ArtistProfile, ArtistManager
from django.utils import timezone



class ArtistProfileSerializer(serializers.ModelSerializer):
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = ArtistProfile
        fields = [
            'id', 'name', 'email', 'bio', 'profile_image', 'profile_image_url',
            'user', 'created_at', 'email_verified', 'status', 'created_by'
        ]
        read_only_fields = ['user', 'created_at', 'email_verified', 'status', 'created_by']

    def get_profile_image_url(self, obj):
        if obj.profile_image:
            return obj.profile_image.url
        return None

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.role == "artist":
            validated_data['user'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop("email_verified", None)
        return super().update(instance, validated_data)

    def validate_email(self, value):
        if value and ArtistProfile.objects.filter(email=value).exclude(
            pk=self.instance.pk if self.instance else None
        ).exists():
            raise serializers.ValidationError("This email is already used.")
        return value


class ArtistManagerSerializer(serializers.ModelSerializer):
    artist_name = serializers.CharField(source='artist.name', read_only=True)
    promoter_name = serializers.CharField(source='promoter.name', read_only=True)

    class Meta:
        model = ArtistManager
        fields = '__all__'
        read_only_fields = ['promoter', 'start_date']

    def validate(self, attrs):
        start_date = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        end_date = attrs.get('end_date', getattr(self.instance, 'end_date', None))
        if end_date and start_date and end_date < start_date:
            raise serializers.ValidationError("End date cannot be before start date.")
        return attrs


class ArtistVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    verification_code = serializers.CharField(max_length=20)

    def validate(self, data):
        email = data.get('email')
        code = data.get('verification_code')
        try:
            artist = ArtistProfile.objects.get(email=email)
        except ArtistProfile.DoesNotExist:
            raise serializers.ValidationError("Aucun profil artiste associé à cet email.")

        if artist.email_verified:
            raise serializers.ValidationError("Le profil est déjà activé.")

        if artist.verification_code != code:
            raise serializers.ValidationError("Code d'activation invalide.")

        if artist.verification_code_expiry and artist.verification_code_expiry < timezone.now():
            raise serializers.ValidationError("Le code d'activation a expiré.")

        data['artist'] = artist
        return data
