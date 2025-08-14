# accounts/supabase_utils.py
import os
from urllib.parse import urljoin

# pip install supabase
from supabase import create_client, Client
from django.core.files.uploadedfile import UploadedFile

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
SUPABASE_BUCKET = os.environ.get('SUPABASE_BUCKET', 'avatars')

def get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Set SUPABASE_URL and SUPABASE_KEY environment variables")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_avatar_to_supabase(file_obj: UploadedFile, dest_path: str) -> str:
    """
    file_obj: Django UploadedFile (InMemoryUploadedFile / TemporaryUploadedFile)
    dest_path: path in bucket e.g. "avatars/user_12.png"
    returns public URL (requires bucket to be public or use signed URL)
    """
    # Basic validation
    if file_obj.size > 2 * 1024 * 1024:
        raise ValueError("File too large. Max 2MB.")
    allowed_types = ['image/jpeg', 'image/png', 'image/webp']
    if file_obj.content_type not in allowed_types:
        raise ValueError("Unsupported image type. Allowed: jpeg, png, webp")

    client = get_supabase_client()
    content = file_obj.read()
    res = client.storage.from_(SUPABASE_BUCKET).upload(dest_path, content, {'content-type': file_obj.content_type})

    # If bucket is public, construct public URL:
    public_url_res = client.storage.from_(SUPABASE_BUCKET).get_public_url(dest_path)
    if public_url_res and public_url_res.get('publicURL'):
        return public_url_res['publicURL']

    # Otherwise return path (you might generate signed URL instead)
    return urljoin(SUPABASE_URL, f'storage/v1/object/public/{SUPABASE_BUCKET}/{dest_path}')
