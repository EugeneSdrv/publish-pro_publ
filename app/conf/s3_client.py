import os

import aioboto3

from dotenv import load_dotenv

load_dotenv()


class S3AsyncClient:
    _cached_session = None

    def __init__(self):
        self.endpoint_domain = os.getenv("MINIO_DOMAIN")
        self.use_ssl = os.getenv("MINIO_USE_SSL").lower() == "true"
        if S3AsyncClient._cached_session is None:
            S3AsyncClient._cached_session = aioboto3.Session(
                aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
                aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
            )
        self.endpoint_url = self._get_endpoint_url()

    async def __aenter__(self):
        self.s3_client = await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.s3_client.__aexit__(exc_type, exc_val, exc_tb)

    @property
    def client(self):
        return S3AsyncClient._cached_session.client(
            "s3", endpoint_url=self.endpoint_url, use_ssl=self.use_ssl
        )

    async def get_client(self):
        try:
            async with self as client:
                return client.s3_client
        except Exception as e:
            raise e

    def _get_endpoint_url(self) -> str:
        if self.endpoint_domain.startswith("http"):
            raise ValueError(
                "settings.MINIO_DOMAIN should not start with 'http' or 'https'. Please use just the domain name."
            )
        protocol = "https" if self.use_ssl else "http"
        return f"{protocol}://{self.endpoint_domain}"


s3client = S3AsyncClient()
