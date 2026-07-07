import os
from dataclasses import dataclass


@dataclass
class Settings:
    api_key: str
    payment_driver: str
    allowed_hosts: list[str]
    version: str


def load_settings() -> Settings:
    hosts = [host.strip() for host in os.getenv("LOCAL_NODE_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")]
    hosts = [host for host in hosts if host]
    return Settings(
        api_key=os.getenv("LOCAL_NODE_API_KEY", ""),
        payment_driver=os.getenv("LOCAL_NODE_PAYMENT_DRIVER", "mock"),
        allowed_hosts=hosts,
        version=os.getenv("LOCAL_NODE_VERSION", "0.1.0"),
    )
