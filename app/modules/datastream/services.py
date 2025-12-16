import asyncio
import json
from dataclasses import dataclass
from typing import Dict, Literal, Optional, Set, Union

from aio_pika.abc import AbstractIncomingMessage
from fastapi import WebSocket
from pydantic import BaseModel, field_validator

from app.modules.rabbitmq import RabbitMQ

DataType = Literal["eeg", "wristband", "emotion", "cognition", "all"]
ALL_DATA_TYPES: Set[DataType] = {
    "eeg",
    "wristband",
    "emotion",
    "cognition",
}


class SubscribeKey(BaseModel):
    subscriptions: Dict[str, Set[DataType]]

    @field_validator("subscriptions", mode="before")
    @classmethod
    def validate_subscriptions(cls, v):
        """支持多种订阅格式的规范化处理
        """
        if not isinstance(v, dict):
            raise TypeError("subscriptions must be a dict")

        normalized: Dict[str, Set[DataType]] = {}

        for stu_id, types in v.items():
            if isinstance(types, str):
                type_set = {types}
            elif isinstance(types, (list, set, tuple)):
                type_set = set(types)
            else:
                raise TypeError("Invalid subscription value for {student_id}: {types}")

            if "all" in type_set:
                normalized[stu_id] = set(ALL_DATA_TYPES)
            else:
                normalized[stu_id] = type_set

        return normalized

    def match(self, *, student_id: str, data_type: DataType) -> bool:
        types = self.subscriptions.get(student_id)
        return types is not None and data_type in types

    def add(self, student_id: str, types: Set[DataType]):
        self.subscriptions.setdefault(student_id, set()).update(types)

    def remove(self, student_id: str, types: Set[DataType]):
        if student_id not in self.subscriptions:
            return
        self.subscriptions[student_id] -= types
        if not self.subscriptions[student_id]:
            del self.subscriptions[student_id]


class SubscribeRequest(SubscribeKey):
    msg_type: Literal["subscribe", "subscribe_add", "subscribe_remove"]


req = SubscribeRequest(**{
    "msg_type": "subscribe",
    "subscriptions": {
        "student1": ["eeg", "emotion"],
        "student2": "all"
    }
})


@dataclass(slots=True)
class _WSConn:
    """
    封装单个 WebSocket 连接，避免直接以 WebSocket 作为 dict value
    """
    ws: WebSocket
    key: Optional[SubscribeKey] = None


class WebsocketManager:
    """
    应用级 WebSocket 管理器（并发安全）
    - 生命周期由 FastAPI app.state 管理
    - 支持 RabbitMQ 回调并发 publish
    """

    def __init__(self):
        self._connections: Dict[int, _WSConn] = {}
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self._connections[id(ws)] = _WSConn(ws=ws)

    async def disconnect(self, ws: WebSocket):
        async with self._lock:
            self._connections.pop(id(ws))

    async def send_text(self, message: str, ws: WebSocket):
        try:
            await ws.send_text(message)
        except Exception:
            await self.disconnect(ws)

    async def send_bytes(self, data: bytes, ws: WebSocket):
        try:
            await ws.send_bytes(data)
        except Exception:
            await self.disconnect(ws)

    async def send_json(self, data, ws: WebSocket, *, mode="text"):
        try:
            await ws.send_json(data, mode)
        except Exception:
            await self.disconnect(ws)

    async def broadcast_text(self, message: str):
        async with self._lock:
            conns = list(self._connections.values())

        coros = [
            self.send_text(message, conn.ws)
            for conn in conns
        ]

        if coros:
            await asyncio.gather(*coros, return_exceptions=True)

    async def broadcast_bytes(self, data: bytes):
        async with self._lock:
            conns = list(self._connections.values())

        coros = [
            self.send_bytes(data, conn.ws)
            for conn in conns
        ]

        if coros:
            await asyncio.gather(*coros, return_exceptions=True)

    async def broadcast_json(self, data, *, mode="text"):
        async with self._lock:
            conns = list(self._connections.values())

        coros = [
            self.send_json(data, conn.ws, mode=mode)
            for conn in conns
        ]

        if coros:
            await asyncio.gather(*coros, return_exceptions=True)

    async def handle_subscribe(self, ws: WebSocket, req: SubscribeRequest):
        async with self._lock:
            conn = self._connections.get(id(ws))
            if conn is None:
                return
            if conn.key is None:
                conn.key = SubscribeKey(subscriptions={})
            key = conn.key

            if req.msg_type == "subscribe":
                key.subscriptions = req.subscriptions
            elif req.msg_type == "subscribe_add":
                for sid, types in req.subscriptions.items():
                    key.add(sid, types)
            elif req.msg_type == "subscribe_remove":
                for sid, types in req.subscriptions.items():
                    key.remove(sid, types)

    async def publish(self, *, student_id: str, data_type: DataType, payload: Union[bytes, dict]):
        async with self._lock:
            coons = list(self._connections.values())

        coros = []
        for coon in coons:
            key = coon.key
            if key is None or not key.match(student_id=student_id, data_type=data_type):
                continue

            if data_type in ("eeg", "wristband"):
                coros.append(coon.ws.send_bytes(payload))
            else:
                coros.append(coon.ws.send_json(payload))

        if coros:
            await asyncio.gather(*coros, return_exceptions=True)

    async def on_rabbitmq_msg(self, message: AbstractIncomingMessage):
        async with message.process():
            routing_key = message.routing_key  # student.{student_id}.{data_type}
            try:
                _, student_id, data_type = routing_key.split(".")
            except ValueError:
                return

            if data_type in ("eeg", "wristband"):
                payload = message.body
            elif data_type in ("emotion", "cognition"):
                payload = json.loads(message.body)
            else:
                return

            await self.publish(student_id=student_id, data_type=data_type, payload=payload)


async def data_consumer_task(mgr: WebsocketManager):
    """
    从 RabbitMQ 队列中消费学生的生理信号数据
    """
    async with RabbitMQ.get_channel(prefetch_count=10) as channel:
        exchange = await RabbitMQ.get_exchange(channel, "amq.topic")  # MQTT消息使用amp.topic交换机
        queue = await RabbitMQ.declare_queue(channel, "datastream_ws", auto_delete=True)

        # 绑定所有学生的所有数据
        await queue.bind(exchange, routing_key="student.*.*")

        await queue.consume(mgr.on_rabbitmq_msg)

        print("[RabbitMQ] Connected and consuming...")

        try:
            # 保持连接
            await asyncio.Future()
        finally:
            await channel.close()
