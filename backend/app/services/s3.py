"""S3 service for document storage."""

import boto3
from botocore.exceptions import ClientError
from typing import Optional
import mimetypes

from app.core.config import settings


class S3Service:
    """S3 service for file operations."""

    def __init__(self):
        """Initialize S3 client."""
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
        )
        self.bucket = settings.S3_BUCKET

    def upload_file(
        self,
        file_content: bytes,
        file_path: str,
        content_type: Optional[str] = None,
    ) -> bool:
        """
        Upload a file to S3.

        Args:
            file_content: File content as bytes
            file_path: S3 object key (path)
            content_type: Optional content type (auto-detected if not provided)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Auto-detect content type if not provided
            if not content_type:
                content_type, _ = mimetypes.guess_type(file_path)
                content_type = content_type or "application/octet-stream"

            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=file_path,
                Body=file_content,
                ContentType=content_type,
            )

            return True

        except ClientError as e:
            print(f"Error uploading file to S3: {str(e)}")
            return False

    def download_file(self, file_path: str) -> Optional[bytes]:
        """
        Download a file from S3.

        Args:
            file_path: S3 object key (path)

        Returns:
            File content as bytes or None
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=file_path)
            return response["Body"].read()

        except ClientError as e:
            print(f"Error downloading file from S3: {str(e)}")
            return None

    def get_signed_url(self, file_path: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a pre-signed URL for file access.

        Args:
            file_path: S3 object key (path)
            expiration: URL expiration time in seconds (default 1 hour)

        Returns:
            Pre-signed URL or None
        """
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": file_path},
                ExpiresIn=expiration,
            )
            return url

        except ClientError as e:
            print(f"Error generating signed URL: {str(e)}")
            return None

    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from S3.

        Args:
            file_path: S3 object key (path)

        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=file_path)
            return True

        except ClientError as e:
            print(f"Error deleting file from S3: {str(e)}")
            return False

    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in S3.

        Args:
            file_path: S3 object key (path)

        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=file_path)
            return True

        except ClientError:
            return False
