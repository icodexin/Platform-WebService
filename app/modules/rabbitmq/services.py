from contextlib import asynccontextmanager
from typing import Union
from urllib.parse import quote

import aio_pika
from aio_pika.abc import AbstractRobustChannel, AbstractRobustConnection
from aio_pika.pool import Pool

from app.core.config import settings


async def create_mq_connection() -> AbstractRobustConnection:
    username = quote(settings.RABBITMQ_USER, safe='')
    password = quote(settings.RABBITMQ_PASSWORD, safe='')
    host = settings.RABBITMQ_HOST
    port = settings.RABBITMQ_PORT
    return await aio_pika.connect_robust(f"amqp://{username}:{password}@{host}:{port}/")


async def create_mq_channel(
        connection: Union[Pool[AbstractRobustConnection], AbstractRobustConnection]) -> AbstractRobustChannel:
    if isinstance(connection, Pool):
        # when connection is a Pool
        async with connection.acquire() as c:
            return await c.channel()
    else:
        # a single connection
        return await connection.channel()


class RabbitMQ:
    max_connections: int = 2
    max_channels: int = 10
    connection_pool: Pool[AbstractRobustConnection] = Pool(create_mq_connection, max_size=max_connections)
    channel_pool: Pool[AbstractRobustChannel] = Pool(create_mq_channel, connection_pool, max_size=max_channels)

    @classmethod
    @asynccontextmanager
    async def get_channel(cls, prefetch_count: int = 0, prefetch_size: int = 0):
        async with cls.channel_pool.acquire() as channel:
            await channel.set_qos(prefetch_count, prefetch_size)
            yield channel

    @staticmethod
    async def get_exchange(channel: AbstractRobustChannel, name: str, **kwargs):
        return await channel.get_exchange(name, **kwargs)

    @staticmethod
    async def declare_queue(channel: AbstractRobustChannel, name: str, **kwargs):
        return await channel.declare_queue(name, **kwargs)
