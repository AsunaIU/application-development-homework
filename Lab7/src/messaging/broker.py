import os

from faststream.rabbit import RabbitBroker

broker = RabbitBroker(
    url=os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
)
