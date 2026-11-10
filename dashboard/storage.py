import os
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import boto3
from botocore.config import Config
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage


REMOTE_IMAGE_PREFIX = 'supabase://'


class HybridProductMediaStorage(FileSystemStorage):
    def url(self, name):
        if name.startswith(REMOTE_IMAGE_PREFIX):
            if not settings.SUPABASE_PROJECT_URL or not settings.SUPABASE_STORAGE_BUCKET:
                raise ImproperlyConfigured(
                    'Supabase product image URL settings are not configured.'
                )
            image_path = name[len(REMOTE_IMAGE_PREFIX):]
            return (
                f'{settings.SUPABASE_PROJECT_URL}/storage/v1/object/public/'
                f'{quote(settings.SUPABASE_STORAGE_BUCKET, safe="")}/'
                f'{quote(image_path, safe="/")}'
            )
        return super().url(name)


def upload_product_image(uploaded_file):
    access_key = os.environ.get('SUPABASE_STORAGE_S3_ACCESS_KEY_ID')
    secret_key = os.environ.get('SUPABASE_STORAGE_S3_SECRET_ACCESS_KEY')
    missing = [
        name for name, value in (
            ('SUPABASE_PROJECT_URL', settings.SUPABASE_PROJECT_URL),
            ('SUPABASE_STORAGE_BUCKET', settings.SUPABASE_STORAGE_BUCKET),
            ('SUPABASE_STORAGE_S3_ENDPOINT', settings.SUPABASE_STORAGE_S3_ENDPOINT),
            ('SUPABASE_STORAGE_S3_REGION', settings.SUPABASE_STORAGE_S3_REGION),
            ('SUPABASE_STORAGE_S3_ACCESS_KEY_ID', access_key),
            ('SUPABASE_STORAGE_S3_SECRET_ACCESS_KEY', secret_key),
        ) if not value
    ]
    if missing:
        raise ImproperlyConfigured(
            'Product image storage is not configured. Missing: '
            + ', '.join(missing)
        )

    extension = Path(uploaded_file.name).suffix.lower()
    object_key = f'products/{uuid4().hex}{extension}'
    client = boto3.client(
        's3',
        endpoint_url=settings.SUPABASE_STORAGE_S3_ENDPOINT,
        region_name=settings.SUPABASE_STORAGE_S3_REGION,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(
            signature_version='s3v4',
            s3={'addressing_style': 'path'},
        ),
    )
    client.put_object(
        Bucket=settings.SUPABASE_STORAGE_BUCKET,
        Key=object_key,
        Body=uploaded_file,
        ContentType=uploaded_file.content_type or 'application/octet-stream',
    )
    return REMOTE_IMAGE_PREFIX + object_key
