import json
import os
import uuid

from botocore.exceptions import ClientError
from dotenv import load_dotenv
from fastapi import UploadFile, HTTPException
from filetype import filetype

from app.conf.s3_client import s3client

load_dotenv()


class S3ImageManager:

    def __init__(self, bucket_name: str, client, default_acl: str = "public-read"):
        self.bucket_name = bucket_name
        self.default_acl = default_acl
        self._validate_instance_attributes()
        self.client = client

    def _validate_instance_attributes(self):
        required_attributes = ("bucket_name", "default_acl")
        for attr in required_attributes:
            value = getattr(self, attr)
            if value is None:
                raise ValueError(
                    f"The '{attr}' class attribute is required and cannot be None."
                )

    @staticmethod
    def _prepare_path(path: str) -> str:
        """
        Подготавливает путь, добавляя '/' в конец, если его нет.

        Аргументы:
        - path (`str`): Путь к объекту в S3.

        Возвращает:
        - `str`: Подготовленный путь с завершающим '/'.
        """
        if path and not path.endswith("/"):
            path += "/"
        return path

    @staticmethod
    async def _read_file(file: UploadFile) -> tuple[bytes, str]:
        """
        Читает содержимое файла и возвращает его содержимое и имя файла.

        Аргументы:
        - file (`UploadFile`): Загружаемый файл.

        Возвращает:
        - `tuple[bytes, str]`: Кортеж, содержащий байты файла и его имя.
        """
        file_content = await file.read()
        file_name = file.filename
        return file_content, file_name

    async def _generate_unique_uuid_key(self, path: str, file_name: str) -> str | None:
        """
        Генерирует уникальный ключ для файла в S3, на базе UUIDv4.

        Аргументы:
        - s3_client: Клиент S3, используемый для взаимодействия с сервисом.
        - path ('str'): Путь до файла
        - file_name (`str`): Предлагаемое имя файла.

        Возвращает:
        - `str`: Уникальный ключ для файла в S3.
        """
        base_name, extension = os.path.splitext(file_name)
        key = path + f"{uuid.uuid4()}{extension}"
        try:
            await self.client.head_object(Bucket=self.bucket_name, Key=key)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return key
            else:
                raise  # Добавить исключение с предложением попробовать создать еще раз

    async def generate_url(self, key: str, expiration: int = 3600) -> str:
        """
        Генерирует и возвращает URL для доступа к объекту в S3. Если объект публичный,
        возвращает прямой URL, иначе создает подписанный URL с ограниченным сроком действия.

        Аргументы:
        - key (`str`): Ключ (имя) объекта в S3.
        - expiration (`int`, optional): Срок действия подписанного URL в секундах. По умолчанию 3600.

        Возвращает:
        - `str`: URL для доступа к объекту в S3.
        """
        if self.default_acl == "public-read":
            return f"{self.client.meta.endpoint_url}/{self.bucket_name}/{key}"
        try:
            url = await self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expiration,
            )
            return url
        except ClientError as e:
            raise HTTPException(
                status_code=500, detail="Error generating presigned URL"
            ) from e

    async def put_object(self, file: UploadFile, path: str = "", file_type: str = "image") -> str:
        """
        Асинхронно загружает файл в S3 бакет и возвращает ключ (имя) объекта в хранилище.

        Аргументы:
        - file (`UploadFile`): Загружаемый файл.
        - path (`str`, optional): Путь в бакете для размещения файла. По умолчанию "".
        - file_type (`str`, optional): Тип файла. По умолчанию "image".

        Возвращает:
        - `str`: Ключ (имя) объекта в S3.
        """
        file_content, file_name = await self._read_file(file)
        path = self._prepare_path(path)
        kind = filetype.guess(file_content)
        is_image = kind is not None and kind.mime.startswith("image")
        if file_type == "image":
            if not is_image:
                raise HTTPException(status_code=400, detail="Invalid image file")
        key = await self._generate_unique_uuid_key(path, file_name)
        try:
            await self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_content,
                ACL=self.default_acl,
            )
        except ClientError as e:
            raise HTTPException(
                status_code=500, detail="Error uploading file to S3"
            ) from e

        return key


    async def delete_object(self, key: str) -> None:
        """
        Удаляет объект из S3 по заданному ключу.

        Аргументы:
        - key (`str`): Ключ объекта в S3.

        Исключения:
        - HTTPException: Возникает при ошибке удаления объекта в S3, кроме случаев, когда объект не найден.
        """
        try:
            await self.client.delete_object(Bucket=self.bucket_name, Key=key)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code != "NoSuchKey":
                raise HTTPException(
                    status_code=500, detail="Error deleting file from S3"
                ) from e


    async def delete_objects(self, objects_keys: list) -> None:
        """
        Удаляет несколько объектов из S3 по списку ключей.
        # :param objects_keys: Список ключей объектов в S3
        # :return: None
        # :exceptions: HTTPException: Возникает при ошибке удаления объекта в S3, кроме случаев, когда объект не найден.
        """
        objects = [{"Key": key} for key in objects_keys]
        try:
            await self.client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={
                        "Objects": objects,
                        "Quiet": False,  # Измените на True, чтобы не получать информацию о каждом объекте. True значение по дефолту. В варианте с minio не работает
                    },
                )
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code != "NoSuchKey":
                raise HTTPException(
                    status_code=500, detail="Error deleting files from S3"
                ) from e


class S3StorageManager:
    buckets = [
        "post-illustration-images",
        "users-avatar-images",
    ]

    # Политика, дающая public read доступ к объектам бакета
    def make_public_policy(self, bucket_name: str) -> str:

        policy = {  # измененная политика
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": ["s3:GetObject", "DeleteObject"],
                    "Resource": [
                        f"arn:aws:s3:::{bucket_name}",
                        f"arn:aws:s3:::{bucket_name}/*",
                    ],
                }
            ],
        }
        return json.dumps(policy)

    async def initialize_buckets(
        self,
    ):
        async with s3client.client as s3conn:
            for bucket_name in self.buckets:
                if not await self.bucket_exists(bucket_name, s3conn):
                    policy = self.make_public_policy(bucket_name)
                    await self.create_bucket(bucket_name, policy, s3conn)
            return "s3 buckets initialised"

    async def create_bucket(self, bucket_name: str, policy: str, s3conn) -> bool:
        try:
            await s3conn.create_bucket(Bucket=bucket_name)
            await s3conn.put_bucket_policy(Bucket=bucket_name, Policy=policy)
            print(f"Bucket {bucket_name} created")
            return True
        except ClientError as e:
            print("Create bucket error:", e)
            return False

    async def bucket_exists(self, bucket_name: str, s3conn) -> bool:
        try:
            # HeadBucket возвращает 200, если бакет доступен
            if await s3conn.head_bucket(Bucket=bucket_name):
                print(f"bucket {bucket_name} already exists")
                return True
        except ClientError as e:
            code = int(e.response["ResponseMetadata"]["HTTPStatusCode"])
            if code == 404:
                return False
            # другие ошибки (403 — доступ запрещён, 301 — неправильный регион и т.д.)
            print("HeadBucket error:", e)
        return False

s3storage_manager = S3StorageManager()
