from collections.abc import AsyncIterator
from typing import Any

import aioboto3

from domain.shared.file_storage import FileStorage
from infrastructure.settings import Settings


class S3FileStorage(FileStorage):
    def __init__(self, settings: Settings) -> None:
        self._bucket = settings.aws_s3_bucket_name
        self._region = settings.aws_s3_region
        self._session = aioboto3.Session(
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_s3_region,
        )
        # endpoint_url vazio → usa AWS real; preenchido → LocalStack ou outro compatível
        self._endpoint_url: str | None = settings.aws_s3_endpoint_url or None

    def _client(self) -> Any:
        return self._session.client("s3", endpoint_url=self._endpoint_url)

    async def save(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        async with self._client() as s3:
            await s3.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
        return key

    async def load_stream(self, key: str) -> AsyncIterator[bytes]:
        async with self._client() as s3:
            response = await s3.get_object(Bucket=self._bucket, Key=key)
            body = response["Body"]

            if hasattr(body, "iter_chunks"):
                async for chunk in body.iter_chunks(chunk_size=65536):
                    yield chunk
                return

            if hasattr(body, "content") and hasattr(body.content, "iter_chunked"):
                async for chunk in body.content.iter_chunked(65536):
                    yield chunk
                return

            while True:
                chunk = await body.read(65536)
                if not chunk:
                    break
                yield chunk

    async def delete(self, key: str) -> None:
        async with self._client() as s3:
            await s3.delete_object(Bucket=self._bucket, Key=key)

    async def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        async with self._client() as s3:
            return await s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=expires_in,
            )
