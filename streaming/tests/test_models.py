#!/usr/bin/env python3
"""
Tests unitaires pour streaming/models.py
"""

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import uuid

from streaming.models import LiveStream, StreamViewer


@pytest.fixture
def artist_user(db, django_user_model):
    """Créer un utilisateur avec le rôle artist"""
    return django_user_model.objects.create_user(
        email='artist@test.com',
        password='testpass123',
        name='Test Artist',
        role='artist'
    )


@pytest.fixture
def promoter_user(db, django_user_model):
    """Créer un utilisateur avec le rôle promoter"""
    return django_user_model.objects.create_user(
        email='promoter@test.com',
        password='testpass123',
        name='Test Promoter',
        role='promoter'
    )


@pytest.fixture
def fan_user(db, django_user_model):
    """Créer un utilisateur avec le rôle fan"""
    return django_user_model.objects.create_user(
        email='fan@test.com',
        password='testpass123',
        name='Test Fan',
        role='fan'
    )


@pytest.fixture
def live_stream(db, artist_user):
    """Créer un stream de base"""
    return LiveStream.objects.create(
        created_by=artist_user,
        title='Test Stream',
        description='Test Description',
        stream_mode='obs',
        ingest_endpoint='rtmp://test.com/ingest',
        playback_url='https://test.com/playback.m3u8',
        channel_arn='arn:aws:ivs:channel/test'
    )


@pytest.fixture
def paid_stream(db, artist_user):
    """Créer un stream payant"""
    return LiveStream.objects.create(
        created_by=artist_user,
        title='Paid Stream',
        description='Paid stream description',
        is_paid=True,
        ticket_price=Decimal('9.99')
    )


@pytest.fixture
def webrtc_stream(db, promoter_user):
    """Créer un stream WebRTC"""
    return LiveStream.objects.create(
        created_by=promoter_user,
        title='WebRTC Stream',
        stream_mode='webcam'
    )


# ======= TESTS POUR LiveStream =========================

@pytest.mark.django_db
class TestLiveStreamCreation:
    """Tests de création du modèle LiveStream"""

    def test_create_stream_with_artist(self, artist_user):
        """Test création d'un stream par un artiste"""
        stream = LiveStream.objects.create(
            created_by=artist_user,
            title='My First Stream',
            description='This is a test stream'
        )

        assert stream.id is not None
        assert isinstance(stream.id, uuid.UUID)
        assert stream.created_by == artist_user
        assert stream.title == 'My First Stream'
        assert stream.description == 'This is a test stream'
        assert stream.stream_mode == 'obs'
        assert stream.status == 'idle'
        assert stream.viewer_count == 0
        assert stream.peak_viewers == 0
        assert stream.is_paid is False
        assert stream.ticket_price == Decimal('0.00')

    def test_create_stream_with_promoter(self, promoter_user):
        """Test création d'un stream par un promoter"""
        stream = LiveStream.objects.create(
            created_by=promoter_user,
            title='Promoter Stream'
        )

        assert stream.created_by == promoter_user
        assert stream.id is not None

    def test_stream_key_auto_generated(self, artist_user):
        """Test génération automatique du stream_key"""
        stream = LiveStream.objects.create(
            created_by=artist_user,
            title='Test Stream'
        )

        assert stream.stream_key is not None
        assert len(stream.stream_key) > 0
        assert isinstance(uuid.UUID(stream.stream_key), uuid.UUID)

    def test_stream_key_uniqueness(self, artist_user):
        """Test unicité du stream_key"""
        stream1 = LiveStream.objects.create(
            created_by=artist_user,
            title='Stream 1'
        )
        stream2 = LiveStream.objects.create(
            created_by=artist_user,
            title='Stream 2'
        )

        assert stream1.stream_key != stream2.stream_key

    def test_created_at_auto_set(self, artist_user):
        """Test que created_at est automatiquement défini"""
        stream = LiveStream.objects.create(
            created_by=artist_user,
            title='Test Stream'
        )

        assert stream.created_at is not None
        assert stream.created_at <= timezone.now()


@pytest.mark.django_db
class TestLiveStreamValidation:
    """Tests de validation du modèle LiveStream"""

    def test_fan_cannot_create_stream(self, fan_user):
        """Test qu'un fan ne peut pas créer de stream"""
        with pytest.raises(ValidationError) as exc_info:
            LiveStream.objects.create(
                created_by=fan_user,
                title='Fan Stream'
            )

        assert 'created_by' in exc_info.value.message_dict

    def test_paid_stream_requires_positive_price(self, artist_user):
        """Test qu'un stream payant nécessite un prix > 0"""
        with pytest.raises(ValidationError) as exc_info:
            LiveStream.objects.create(
                created_by=artist_user,
                title='Bad Paid Stream',
                is_paid=True,
                ticket_price=Decimal('0.00')
            )

        assert 'ticket_price' in exc_info.value.message_dict

    def test_paid_stream_negative_price_invalid(self, artist_user):
        """Test qu'un prix négatif est invalide"""
        with pytest.raises(ValidationError) as exc_info:
            LiveStream.objects.create(
                created_by=artist_user,
                title='Negative Price Stream',
                is_paid=True,
                ticket_price=Decimal('-5.00')
            )

        assert 'ticket_price' in exc_info.value.message_dict

    def test_obs_live_requires_endpoints(self, artist_user):
        """Test qu'un stream OBS live nécessite les endpoints"""
        stream = LiveStream.objects.create(
            created_by=artist_user,
            title='OBS Stream',
            stream_mode='obs'
        )

        stream.status = 'live'
        with pytest.raises(ValidationError):
            stream.save()

    def test_webrtc_live_requires_session_id(self, artist_user):
        """Test qu'un stream WebRTC live nécessite session_id"""
        stream = LiveStream.objects.create(
            created_by=artist_user,
            title='WebRTC Stream',
            stream_mode='webcam'
        )

        stream.status = 'live'
        with pytest.raises(ValidationError):
            stream.save()

    def test_valid_obs_live_stream(self, artist_user):
        """Test création valide d'un stream OBS live"""
        stream = LiveStream.objects.create(
            created_by=artist_user,
            title='Valid OBS Stream',
            stream_mode='obs',
            ingest_endpoint='rtmp://example.com/ingest',
            playback_url='https://example.com/playback.m3u8',
            channel_arn='arn:aws:ivs:us-west-2:123456789012:channel/abcd'
        )

        stream.status = 'live'
        stream.save()  # Ne devrait pas lever d'exception
        assert stream.status == 'live'

    def test_valid_webrtc_live_stream(self, promoter_user):
        """Test création valide d'un stream WebRTC live"""
        stream = LiveStream.objects.create(
            created_by=promoter_user,
            title='Valid WebRTC Stream',
            stream_mode='webcam',
            webrtc_session_id='session-123'
        )

        stream.status = 'live'
        stream.save()  # Ne devrait pas lever d'exception
        assert stream.status == 'live'


@pytest.mark.django_db
class TestLiveStreamLifecycle:
    """Tests du cycle de vie du stream"""

    def test_go_live(self, live_stream):
        """Test transition vers le statut live"""
        assert live_stream.status == 'idle'
        assert live_stream.started_at is None

        live_stream.go_live()

        assert live_stream.status == 'live'
        assert live_stream.started_at is not None
        assert live_stream.viewer_count == 0

    def test_go_live_idempotent(self, live_stream):
        """Test que go_live est idempotent"""
        live_stream.go_live()
        first_started_at = live_stream.started_at

        live_stream.go_live()

        assert live_stream.started_at == first_started_at

    def test_end_stream(self, live_stream):
        """Test fin du stream"""
        live_stream.go_live()
        assert live_stream.status == 'live'

        live_stream.end_stream()

        assert live_stream.status == 'ended'
        assert live_stream.ended_at is not None
        assert live_stream.viewer_count == 0

    def test_end_stream_idempotent(self, live_stream):
        """Test que end_stream est idempotent"""
        live_stream.go_live()
        live_stream.end_stream()
        first_ended_at = live_stream.ended_at

        live_stream.end_stream()

        assert live_stream.ended_at == first_ended_at


@pytest.mark.django_db
class TestLiveStreamViewerManagement:
    """Tests de gestion des viewers"""

    def test_increment_viewers(self, live_stream):
        """Test incrémentation du nombre de viewers"""
        assert live_stream.viewer_count == 0

        live_stream.increment_viewers()

        assert live_stream.viewer_count == 1

    def test_increment_viewers_multiple(self, live_stream):
        """Test incrémentation de plusieurs viewers"""
        live_stream.increment_viewers(5)

        assert live_stream.viewer_count == 5

    def test_increment_viewers_updates_peak(self, live_stream):
        """Test que peak_viewers est mis à jour"""
        live_stream.increment_viewers(10)

        assert live_stream.viewer_count == 10
        assert live_stream.peak_viewers == 10

    def test_peak_viewers_not_decreased(self, live_stream):
        """Test que peak_viewers ne diminue pas"""
        live_stream.increment_viewers(10)
        assert live_stream.peak_viewers == 10

        live_stream.decrement_viewers(5)

        assert live_stream.viewer_count == 5
        assert live_stream.peak_viewers == 10

    def test_decrement_viewers(self, live_stream):
        """Test décrémentation du nombre de viewers"""
        live_stream.increment_viewers(5)

        live_stream.decrement_viewers(2)

        assert live_stream.viewer_count == 3

    def test_decrement_viewers_never_negative(self, live_stream):
        """Test que viewer_count ne devient jamais négatif"""
        live_stream.viewer_count = 2

        live_stream.decrement_viewers(5)

        assert live_stream.viewer_count == 0

    def test_update_peak_viewers(self, live_stream):
        """Test mise à jour manuelle de peak_viewers"""
        live_stream.peak_viewers = 10
        live_stream.save()

        live_stream.update_peak_viewers(15)

        assert live_stream.peak_viewers == 15

    def test_update_peak_viewers_not_decreased(self, live_stream):
        """Test que update_peak_viewers ne diminue pas la valeur"""
        live_stream.peak_viewers = 20
        live_stream.save()

        live_stream.update_peak_viewers(10)

        assert live_stream.peak_viewers == 20


@pytest.mark.django_db
class TestLiveStreamProperties:
    """Tests des propriétés du modèle LiveStream"""

    def test_duration_not_started(self, live_stream):
        """Test duration quand le stream n'a pas commencé"""
        assert live_stream.duration is None

    def test_duration_live(self, live_stream):
        """Test duration d'un stream en cours"""
        live_stream.go_live()

        duration = live_stream.duration

        assert duration is not None
        assert duration.total_seconds() >= 0

    def test_duration_ended(self, live_stream):
        """Test duration d'un stream terminé"""
        live_stream.started_at = timezone.now() - timedelta(hours=2)
        live_stream.ended_at = timezone.now()
        live_stream.save()

        duration = live_stream.duration

        assert duration is not None
        assert duration.total_seconds() > 7000  # Environ 2 heures

    def test_is_live_property(self, live_stream):
        """Test propriété is_live"""
        assert live_stream.is_live is False

        live_stream.go_live()

        assert live_stream.is_live is True

        live_stream.end_stream()

        assert live_stream.is_live is False

    def test_is_free_property(self, live_stream, paid_stream):
        """Test propriété is_free"""
        assert live_stream.is_free is True
        assert paid_stream.is_free is False


@pytest.mark.django_db
class TestLiveStreamStr:
    """Tests de la représentation string"""

    def test_str_representation(self, live_stream):
        """Test __str__ du stream"""
        result = str(live_stream)

        assert 'Test Stream' in result
        assert 'Test Artist' in result
        assert 'Idle' in result


@pytest.mark.django_db
class TestLiveStreamOrdering:
    """Tests de l'ordre par défaut"""

    def test_default_ordering(self, artist_user):
        """Test que les streams sont ordonnés par date de création DESC"""
        stream1 = LiveStream.objects.create(
            created_by=artist_user,
            title='First Stream'
        )
        stream2 = LiveStream.objects.create(
            created_by=artist_user,
            title='Second Stream'
        )

        streams = list(LiveStream.objects.all())

        assert streams[0] == stream2
        assert streams[1] == stream1


# ================= TESTS POUR StreamViewer ========================

@pytest.mark.django_db
class TestStreamViewerCreation:
    """Tests de création du modèle StreamViewer"""

    def test_create_viewer_authenticated(self, live_stream, fan_user):
        """Test création d'un viewer authentifié"""
        viewer = StreamViewer.objects.create(
            stream=live_stream,
            viewer=fan_user,
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0'
        )

        assert viewer.id is not None
        assert isinstance(viewer.id, uuid.UUID)
        assert viewer.stream == live_stream
        assert viewer.viewer == fan_user
        assert viewer.session_id is not None
        assert viewer.ip_address == '192.168.1.1'
        assert viewer.user_agent == 'Mozilla/5.0'
        assert viewer.joined_at is not None
        assert viewer.left_at is None
        assert viewer.duration_seconds == 0

    def test_create_viewer_anonymous(self, live_stream):
        """Test création d'un viewer anonyme"""
        viewer = StreamViewer.objects.create(
            stream=live_stream,
            viewer=None,
            ip_address='10.0.0.1'
        )

        assert viewer.viewer is None
        assert viewer.ip_address == '10.0.0.1'

    def test_session_id_auto_generated(self, live_stream, fan_user):
        """Test génération automatique du session_id"""
        viewer = StreamViewer.objects.create(
            stream=live_stream,
            viewer=fan_user
        )

        assert viewer.session_id is not None
        assert isinstance(viewer.session_id, uuid.UUID)

    def test_session_id_uniqueness(self, live_stream, fan_user):
        """Test unicité des session_id"""
        viewer1 = StreamViewer.objects.create(
            stream=live_stream,
            viewer=fan_user
        )
        viewer2 = StreamViewer.objects.create(
            stream=live_stream,
            viewer=fan_user
        )

        assert viewer1.session_id != viewer2.session_id


@pytest.mark.django_db
class TestStreamViewerLifecycle:
    """Tests du cycle de vie d'un viewer"""

    def test_mark_left(self, live_stream, fan_user):
        """Test marquage de départ d'un viewer"""
        viewer = StreamViewer.objects.create(
            stream=live_stream,
            viewer=fan_user
        )

        assert viewer.left_at is None
        assert viewer.duration_seconds == 0

        viewer.mark_left()

        assert viewer.left_at is not None
        assert viewer.duration_seconds > 0

    def test_mark_left_idempotent(self, live_stream, fan_user):
        """Test que mark_left est idempotent"""
        viewer = StreamViewer.objects.create(
            stream=live_stream,
            viewer=fan_user
        )

        viewer.mark_left()
        first_left_at = viewer.left_at
        first_duration = viewer.duration_seconds

        viewer.mark_left()

        assert viewer.left_at == first_left_at
        assert viewer.duration_seconds == first_duration

    def test_duration_calculation(self, live_stream, fan_user):
        """Test calcul de la durée de visionnage"""
        viewer = StreamViewer.objects.create(
            stream=live_stream,
            viewer=fan_user
        )

        # Simuler un visionnage de quelques secondes
        viewer.joined_at = timezone.now() - timedelta(seconds=30)
        viewer.save()

        viewer.mark_left()

        assert viewer.duration_seconds >= 30
        assert viewer.duration_seconds <= 35  # Avec marge


@pytest.mark.django_db
class TestStreamViewerProperties:
    """Tests des propriétés du modèle StreamViewer"""

    def test_is_active_true(self, live_stream, fan_user):
        """Test is_active pour un viewer actif"""
        viewer = StreamViewer.objects.create(
            stream=live_stream,
            viewer=fan_user
        )

        assert viewer.is_active is True

    def test_is_active_false(self, live_stream, fan_user):
        """Test is_active pour un viewer parti"""
        viewer = StreamViewer.objects.create(
            stream=live_stream,
            viewer=fan_user
        )

        viewer.mark_left()

        assert viewer.is_active is False


@pytest.mark.django_db
class TestStreamViewerStr:
    """Tests de la représentation string"""

    def test_str_authenticated_viewer(self, live_stream, fan_user):
        """Test __str__ pour un viewer authentifié"""
        viewer = StreamViewer.objects.create(
            stream=live_stream,
            viewer=fan_user
        )

        result = str(viewer)

        assert 'Test Fan' in result
        assert 'Test Stream' in result

    def test_str_anonymous_viewer(self, live_stream):
        """Test __str__ pour un viewer anonyme"""
        viewer = StreamViewer.objects.create(
            stream=live_stream,
            viewer=None
        )

        result = str(viewer)

        assert 'Anonymous' in result
        assert 'Test Stream' in result


@pytest.mark.django_db
class TestStreamViewerRelationships:
    """Tests des relations entre modèles"""

    def test_stream_views_relationship(self, live_stream, fan_user, artist_user):
        """Test relation inverse stream.views"""
        viewer1 = StreamViewer.objects.create(
            stream=live_stream,
            viewer=fan_user
        )
        viewer2 = StreamViewer.objects.create(
            stream=live_stream,
            viewer=artist_user
        )

        views = live_stream.views.all()

        assert views.count() == 2
        assert viewer1 in views
        assert viewer2 in views

    def test_user_stream_views_relationship(self, live_stream, webrtc_stream, fan_user):
        """Test relation inverse user.stream_views"""
        viewer1 = StreamViewer.objects.create(
            stream=live_stream,
            viewer=fan_user
        )
        viewer2 = StreamViewer.objects.create(
            stream=webrtc_stream,
            viewer=fan_user
        )

        views = fan_user.stream_views.all()

        assert views.count() == 2
        assert viewer1 in views
        assert viewer2 in views

    def test_cascade_delete_stream(self, live_stream, fan_user):
        """Test suppression en cascade du stream"""
        viewer = StreamViewer.objects.create(
            stream=live_stream,
            viewer=fan_user
        )
        viewer_id = viewer.id

        live_stream.delete()

        assert not StreamViewer.objects.filter(id=viewer_id).exists()

    def test_set_null_delete_user(self, live_stream, fan_user):
        """Test SET_NULL lors de la suppression d'un user"""
        viewer = StreamViewer.objects.create(
            stream=live_stream,
            viewer=fan_user
        )

        fan_user.delete()
        viewer.refresh_from_db()

        assert viewer.viewer is None


# =============== TESTS D'INTÉGRATION ===========================

@pytest.mark.django_db
class TestIntegration:
    """Tests d'intégration entre les modèles"""

    def test_complete_stream_lifecycle(self, artist_user, fan_user):
        """Test cycle de vie complet d'un stream"""
        # Création du stream
        stream = LiveStream.objects.create(
            created_by=artist_user,
            title='Complete Stream Test',
            stream_mode='obs',
            ingest_endpoint='rtmp://test.com/ingest',
            playback_url='https://test.com/playback.m3u8'
        )

        # Démarrage
        stream.go_live()
        assert stream.is_live

        # Ajout de viewers
        viewer1 = StreamViewer.objects.create(stream=stream, viewer=fan_user)
        stream.increment_viewers()

        viewer2 = StreamViewer.objects.create(stream=stream, viewer=None)
        stream.increment_viewers()

        assert stream.viewer_count == 2
        assert stream.peak_viewers == 2

        # Un viewer part
        viewer1.mark_left()
        stream.decrement_viewers()

        assert stream.viewer_count == 1
        assert stream.peak_viewers == 2  # Peak reste à 2

        # Fin du stream
        stream.end_stream()
        assert not stream.is_live
        assert stream.viewer_count == 0
        assert stream.duration is not None

    def test_paid_stream_workflow(self, promoter_user):
        """Test workflow d'un stream payant"""
        stream = LiveStream.objects.create(
            created_by=promoter_user,
            title='Paid Concert',
            is_paid=True,
            ticket_price=Decimal('19.99')
        )

        assert not stream.is_free
        assert stream.ticket_price == Decimal('19.99')
        assert stream.created_by.role == 'promoter'
