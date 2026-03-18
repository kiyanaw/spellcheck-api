"""
FST file management - handles downloading and caching FST files from S3 to EFS.

Files are cached on EFS, but we check S3 ETag to detect when files have been
updated and need to be re-downloaded.
"""

import os

EFS_MOUNT = '/mnt/fsts'
BUCKET_NAME = os.environ.get('FST_BUCKET_NAME')
REGION = os.environ.get('REGION', 'us-east-1')


def _get_etag_path(file_name):
    return os.path.join(EFS_MOUNT, f'{file_name}.etag')


def _read_stored_etag(file_name):
    try:
        etag_path = _get_etag_path(file_name)
        if os.path.exists(etag_path):
            with open(etag_path, 'r') as f:
                return f.read().strip()
    except Exception as e:
        print(f'Warning: Failed to read ETag for {file_name}: {e}')
    return None


def _store_etag(file_name, etag):
    try:
        etag_path = _get_etag_path(file_name)
        with open(etag_path, 'w') as f:
            f.write(etag)
    except Exception as e:
        print(f'Warning: Failed to store ETag for {file_name}: {e}')


def _get_s3_etag(s3_client, s3_key):
    from botocore.exceptions import ClientError
    try:
        response = s3_client.head_object(Bucket=BUCKET_NAME, Key=s3_key)
        etag = response.get('ETag', '')
        return etag.replace('"', '')
    except ClientError as e:
        if e.response['Error']['Code'] in ('404', 'NoSuchKey', 'NotFound'):
            return None
        raise


def download_fst_from_s3(file_name):
    """
    Download FST file from S3 to EFS mount point.

    Checks S3 ETag against stored ETag to detect file updates.
    Re-downloads if the file doesn't exist locally or if the S3 version is newer.

    Returns the local EFS path to the downloaded file.
    """
    import boto3
    from botocore.exceptions import ClientError

    if not BUCKET_NAME:
        raise RuntimeError('FST_BUCKET_NAME environment variable is not set')

    s3_key = file_name
    local_path = os.path.join(EFS_MOUNT, file_name)

    # Ensure EFS directory exists
    os.makedirs(EFS_MOUNT, exist_ok=True)

    s3_client = boto3.client('s3', region_name=REGION)

    # Get ETag from S3
    s3_etag = _get_s3_etag(s3_client, s3_key)
    if not s3_etag:
        raise FileNotFoundError(f'FST file not found in S3: {s3_key}')

    # Check if file exists locally and compare ETags
    stored_etag = _read_stored_etag(file_name)
    file_exists = os.path.exists(local_path)

    if not stored_etag:
        if file_exists:
            print(f'FST file {file_name} exists but has no ETag. Re-downloading to create ETag...')
            try:
                os.unlink(local_path)
            except Exception as e:
                print(f'Warning: Failed to remove old file {file_name}: {e}')
    elif file_exists and stored_etag == s3_etag:
        # File exists and ETags match - use cached version
        return local_path
    elif file_exists and stored_etag != s3_etag:
        print(f'FST file {file_name} has been updated in S3 (ETag changed). Re-downloading...')
        try:
            os.unlink(local_path)
            etag_path = _get_etag_path(file_name)
            if os.path.exists(etag_path):
                os.unlink(etag_path)
        except Exception as e:
            print(f'Warning: Failed to remove old file {file_name}: {e}')

    try:
        s3_client.download_file(BUCKET_NAME, s3_key, local_path)
        _store_etag(file_name, s3_etag)
        print(f'Downloaded FST file {file_name} from S3')
        return local_path
    except ClientError as e:  # noqa: F821 — imported above in this function
        if e.response['Error']['Code'] in ('404', 'NoSuchKey'):
            raise FileNotFoundError(f'FST file not found: {s3_key}')
        raise RuntimeError(f'Failed to download FST file {s3_key}: {e}')
