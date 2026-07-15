import os

from qcloud_cos import CosConfig, CosS3Client


class CosClient:

    _cos_client = None


    @classmethod
    def get_cos_client(cls):
        if cls._cos_client is None:
            cos_config = CosConfig(
                SecretId=os.getenv("COS_SECRET_ID"),
                SecretKey=os.getenv("COS_SECRET_KEY"),
                Region=os.getenv("COS_REGION"),
                Scheme=os.getenv("COS_SCHEME")
            )
            cls._cos_client = CosS3Client(cos_config)
        return cls._cos_client

    @classmethod
    def get_bucket_name(cls):
        return os.getenv("COS_BUCKET")

cos_client = CosClient.get_cos_client()