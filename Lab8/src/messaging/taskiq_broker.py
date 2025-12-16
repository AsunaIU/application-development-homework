import os
from typing import List
from taskiq_aio_pika import AioPikaBroker
from taskiq import TaskiqScheduler, ScheduleSource
from taskiq.schedule_sources import LabelScheduleSource


taskiq_broker = AioPikaBroker(
    url=os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/"),
)


scheduler = TaskiqScheduler(
    broker=taskiq_broker,
    sources=[LabelScheduleSource(taskiq_broker)],
)
