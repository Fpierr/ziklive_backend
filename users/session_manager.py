import os
import uuid
import json
from cryptography.fernet import Fernet
from django.core.cache import cache
from django.conf import settings
#from ziklive_backend import settings

fernet_key = os.getenv('FERNET_SECRET_KEY').encode()
fernet = Fernet(fernet_key)

timeout = settings.SESSION_REDIS_TTL

def create_session(user_id: int, csrf_token: str, jti: str) -> str:
    session_id = str(uuid.uuid4())
    session_data = json.dumps({
        'user_id': user_id,
        'csrf_token': csrf_token,
        'refresh_jti': jti,
    })

    encrypted = fernet.encrypt(session_data.encode())
    cache.set(session_id, encrypted , timeout=timeout)
    return session_id

def get_session(session_id: str) -> dict:
    encrypted = cache.get(session_id)
    if not encrypted:
        return None
    try:
        decrypted = fernet.decrypt(encrypted).decode()
        return json.loads(decrypted)
    except Exception as e:
        return None


def delete_session(session_id: str):
    cache.delete(session_id)
