import asyncio
import pytest
from faststream.rabbit import RabbitBroker

RABBITMQ_URL = "amqp://guest:guest@localhost:5672/"


@pytest.fixture
async def broker():
    """Fixture to create and cleanup broker"""
    broker = RabbitBroker(RABBITMQ_URL)
    await broker.start()
    yield broker
    await broker.stop()


@pytest.mark.asyncio
async def test_rabbitmq_connection(broker):
    """Test basic RabbitMQ connection"""
    assert broker._connection is not None


@pytest.mark.asyncio
async def test_rabbitmq_publish_subscribe(broker):
    """Test publish and subscribe functionality"""
    received_messages = []

    @broker.subscriber("test_queue")
    async def handle(msg):
        received_messages.append(msg)

    await broker.start()

    test_message = "Hello from pytest!"
    await broker.publish(test_message, "test_queue")

    await asyncio.sleep(1)

    assert len(received_messages) == 1
    assert received_messages[0] == test_message


@pytest.mark.asyncio
async def test_rabbitmq_multiple_messages(broker):
    """Test multiple messages"""
    received_messages = []

    @broker.subscriber("multi_queue")
    async def handle(msg):
        received_messages.append(msg)

    await broker.start()

    messages = ["msg1", "msg2", "msg3"]
    for msg in messages:
        await broker.publish(msg, "multi_queue")

    await asyncio.sleep(2)

    assert len(received_messages) == len(messages)
    assert received_messages == messages


def test_rabbitmq_service_running():
    """Test if RabbitMQ service is accessible"""
    import socket

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(("localhost", 5672))
        sock.close()

        assert result == 0, "RabbitMQ port 5672 is not accessible"
    except Exception as e:
        pytest.fail(f"Cannot reach RabbitMQ: {e}")
