#import os
from django.core.mail import send_mail
from django.conf import settings
#from ziklive_backend import settings


def send_verification_email(artist):
    message = (
        f"Bonjour {artist.name},\n\n"
        "Votre profil artiste a été créé sur ZikLive.\n"
        "Pour activer votre profil, veuillez vous connecter et entrer le code d'activation ci-dessous.\n"
        f"Code d'activation : {artist.verification_code}\n\n"
        "Ce code est valide pendant 10 jours.\n"
        "Merci de votre confiance.\n\n"
        "L'équipe ZikLive"
    )

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
    if not from_email:
        raise ValueError("DEFAULT_FROM_EMAIL not defined in settings")

    send_mail(
        subject="Activation de votre profil artiste sur ZikLive",
        message=message,
        from_email=from_email,
        recipient_list=[artist.email],
        fail_silently=False,
    )
