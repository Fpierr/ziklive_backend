import string
import random
from datetime import timedelta
from django.utils import timezone
from users.services.email import send_verification_email


def generate_verification_code(artist, length=12):
    chars = string.ascii_letters + string.digits
    code = ''.join(random.choice(chars) for _ in range(length))
    artist.verification_code = code
    artist.verification_code_expiry = timezone.now() + timedelta(days=30)
    artist.save()
    return code


def trigger_verification_flow(artist):
    generate_verification_code(artist)
    send_verification_email(artist)
