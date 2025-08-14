# posts/supabase_utils.py
import os
from urllib.parse import urljoin
from django.core.files.uploadedfile import UploadedFile

# pip install supabase
from supabase import create_client, Client

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SUPABASE_BUCKET = os.getenv('SUPABASE_BUCKET', 'posts')  # default bucket posts

def get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError('SUPABASE_URL and SUPABASE_KEY must be set as env variables')
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_image_to_supabase(file_obj: UploadedFile, dest_path: str) -> str:
    """
    Uploads the file_obj (Django UploadedFile) to Supabase and returns a public URL.
    Raises ValueError on invalid file or size.
    """
    # validate size
    max_size = 2 * 1024 * 1024  # 2MB
    if file_obj.size > max_size:
        raise ValueError('Image too large. Max size is 2MB.')

    # validate content type
    allowed = ('image/jpeg', 'image/png')
    content_type = getattr(file_obj, 'content_type', None)
    if content_type not in allowed:
        raise ValueError('Unsupported file type. Allowed: JPEG, PNG.')

    client = get_supabase_client()
    content = file_obj.read()
    # upload: dest_path e.g. avatars/user_12.png or posts/post_<id>.png
    upload_res = client.storage.from_(SUPABASE_BUCKET).upload(dest_path, content, {'content-type': content_type})
    # get public url
    public = client.storage.from_(SUPABASE_BUCKET).get_public_url(dest_path)
    public_url = public.get('publicURL') if isinstance(public, dict) else None
    if public_url:
        return public_url
    # fallback
    return urljoin(SUPABASE_URL, f'storage/v1/object/public/{SUPABASE_BUCKET}/{dest_path}')
