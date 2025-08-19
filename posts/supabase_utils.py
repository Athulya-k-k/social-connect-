# # posts/supabase_utils.py
# import os
# from urllib.parse import urljoin
# from django.core.files.uploadedfile import UploadedFile

# # pip install supabase
# from supabase import create_client, Client

# SUPABASE_URL = os.getenv('SUPABASE_URL')
# SUPABASE_KEY = os.getenv('SUPABASE_KEY')
# SUPABASE_BUCKET = os.getenv('SUPABASE_BUCKET', 'posts')  # default bucket posts

# def get_supabase_client() -> Client:
#     if not SUPABASE_URL or not SUPABASE_KEY:
#         raise RuntimeError('SUPABASE_URL and SUPABASE_KEY must be set as env variables')
#     return create_client(SUPABASE_URL, SUPABASE_KEY)

# def upload_image_to_supabase(file_obj: UploadedFile, dest_path: str) -> str:
#     """
#     Uploads the file_obj (Django UploadedFile) to Supabase and returns a public URL.
#     Raises ValueError on invalid file or size.
#     """
#     # validate size
#     max_size = 2 * 1024 * 1024  # 2MB
#     if file_obj.size > max_size:
#         raise ValueError('Image too large. Max size is 2MB.')

#     # validate content type
#     allowed = ('image/jpeg', 'image/png')
#     content_type = getattr(file_obj, 'content_type', None)
#     if content_type not in allowed:
#         raise ValueError('Unsupported file type. Allowed: JPEG, PNG.')

#     client = get_supabase_client()
#     content = file_obj.read()
#     # upload: dest_path e.g. avatars/user_12.png or posts/post_<id>.png
#     upload_res = client.storage.from_(SUPABASE_BUCKET).upload(dest_path, content, {'content-type': content_type})
#     # get public url
#     public = client.storage.from_(SUPABASE_BUCKET).get_public_url(dest_path)
#     public_url = public.get('publicURL') if isinstance(public, dict) else None
#     if public_url:
#         return public_url
#     # fallback
#     return urljoin(SUPABASE_URL, f'storage/v1/object/public/{SUPABASE_BUCKET}/{dest_path}')





import os
import logging
from urllib.parse import urljoin
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings

logger = logging.getLogger(__name__)

# Check if supabase is available
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    logger.warning("Supabase not installed. Image uploads will be disabled.")
    SUPABASE_AVAILABLE = False

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SUPABASE_BUCKET = os.getenv('SUPABASE_BUCKET', 'posts')

def get_supabase_client() -> 'Client':
    """Get Supabase client with proper error handling"""
    if not SUPABASE_AVAILABLE:
        raise RuntimeError('Supabase package is not installed. Run: pip install supabase')
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError('SUPABASE_URL and SUPABASE_KEY must be set as environment variables')
    
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {e}")
        raise RuntimeError(f"Failed to connect to Supabase: {e}")

def upload_image_to_supabase(file_obj: UploadedFile, dest_path: str) -> str:
    """
    Uploads the file_obj (Django UploadedFile) to Supabase and returns a public URL.
    Returns None if upload fails to allow posts without images.
    """
    try:
        # Validate file first
        if not validate_image_file(file_obj):
            raise ValueError("Invalid image file")
        
        logger.info(f"Attempting to upload image to Supabase: {dest_path}")
        
        client = get_supabase_client()
        content = file_obj.read()
        
        # Reset file pointer after reading
        file_obj.seek(0)
        
        # Upload file
        logger.info(f"Uploading to bucket: {SUPABASE_BUCKET}, path: {dest_path}")
        
        upload_response = client.storage.from_(SUPABASE_BUCKET).upload(
            dest_path, 
            content, 
            {'content-type': file_obj.content_type}
        )
        
        logger.info(f"Upload response: {upload_response}")
        
        # Get public URL
        public_url_response = client.storage.from_(SUPABASE_BUCKET).get_public_url(dest_path)
        
        if isinstance(public_url_response, dict) and 'publicURL' in public_url_response:
            public_url = public_url_response['publicURL']
        else:
            # Fallback URL construction
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{dest_path}"
        
        logger.info(f"Generated public URL: {public_url}")
        return public_url
        
    except Exception as e:
        logger.error(f"Failed to upload image to Supabase: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"SUPABASE_URL: {SUPABASE_URL}")
        logger.error(f"SUPABASE_KEY: {'Set' if SUPABASE_KEY else 'Not set'}")
        
        # Don't raise the error - allow posts without images
        # You can change this behavior if you want uploads to be mandatory
        return None

def validate_image_file(file_obj: UploadedFile) -> bool:
    """Validate image file size and type"""
    try:
        # Validate size (2MB max)
        max_size = 2 * 1024 * 1024
        if file_obj.size > max_size:
            logger.error(f"File too large: {file_obj.size} bytes (max: {max_size})")
            return False

        # Validate content type
        allowed_types = ('image/jpeg', 'image/png', 'image/jpg')
        if not hasattr(file_obj, 'content_type') or file_obj.content_type not in allowed_types:
            logger.error(f"Invalid content type: {getattr(file_obj, 'content_type', 'Unknown')}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error validating file: {e}")
        return False

# Alternative: Local file storage fallback
def save_image_locally(file_obj: UploadedFile, dest_path: str) -> str:
    """
    Fallback function to save images locally if Supabase fails
    """
    try:
        import os
        from django.conf import settings
        
        # Create media directory if it doesn't exist
        media_root = getattr(settings, 'MEDIA_ROOT', 'media')
        upload_dir = os.path.join(media_root, 'posts')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file locally
        filename = os.path.basename(dest_path)
        local_path = os.path.join(upload_dir, filename)
        
        with open(local_path, 'wb') as f:
            for chunk in file_obj.chunks():
                f.write(chunk)
        
        # Return relative URL
        media_url = getattr(settings, 'MEDIA_URL', '/media/')
        return f"{media_url}posts/{filename}"
        
    except Exception as e:
        logger.error(f"Failed to save image locally: {e}")
        return None