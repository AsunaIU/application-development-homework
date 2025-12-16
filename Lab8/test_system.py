import asyncio
import json
import os
import sys

import httpx
from aio_pika import DeliveryMode, Message, connect_robust


async def check_api_health():
    """Проверка доступности API"""
    print("\n" + "=" * 60)
    print("ПРОВЕРКА ДОСТУПНОСТИ API")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/users", timeout=5.0)
            if response.status_code == 200:
                print("API доступен")
                return True
            else:
                print(f"API статус: {response.status_code}")
                return False
        except httpx.ConnectError:
            print("API недоступен")
            return False


async def create_test_user():
    """Создание тестового пользователя"""
    base_url = "http://localhost:8000"

    print("создание тестового пользователя")

    user_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "full_name": "Test User",
        "is_active": True,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{base_url}/users", json=user_data, timeout=10.0
            )

            if response.status_code in (200, 201):
                user = response.json()
                print(f"Пользователь создан успешно!")
                print(f"ID: {user['id']}")
                print(f"Username: {user['username']}")
                print(f"Email: {user['email']}")
                return user["id"]
            elif response.status_code == 409:
                print("Пользователь существует, получаем ID...")
                list_response = await client.get(f"{base_url}/users")
                if list_response.status_code == 200:
                    users = list_response.json()
                    for user in users.get("items", []):
                        if user["username"] == "testuser":
                            print(f"Найден существующий пользователь!")
                            print(f"ID: {user['id']}")
                            return user["id"]
                return 1
            else:
                print(f"Ошибка создания пользователя: {response.status_code}")
                print(f"{response.text}")
                return None

        except httpx.ConnectError:
            print("Не удалось подключиться к API")
            return None
        except Exception as e:
            print(f"Ошибка: {e}")
            return None


async def send_message(channel, queue_name: str, message: dict):
    """Отправка сообщения в указанную очередь"""
    await channel.default_exchange.publish(
        Message(
            body=json.dumps(message).encode(),
            delivery_mode=DeliveryMode.PERSISTENT,
        ),
        routing_key=queue_name,
    )
    print(f"Отправлено в '{queue_name}': {message}")


async def create_products(channel):
    """Создание 5 продуктов"""
    print("Создание продуктов")

    products = [
        {
            "action": "create",
            "data": {
                "name": "Laptop Dell XPS 15",
                "price": 1299.99,
                "stock_quantity": 25,
            },
        },
        {
            "action": "create",
            "data": {
                "name": "Wireless Mouse Logitech MX",
                "price": 79.99,
                "stock_quantity": 150,
            },
        },
        {
            "action": "create",
            "data": {
                "name": "Mechanical Keyboard",
                "price": 149.99,
                "stock_quantity": 75,
            },
        },
        {
            "action": "create",
            "data": {"name": "USB-C Hub 7-in-1", "price": 49.99, "stock_quantity": 200},
        },
        {
            "action": "create",
            "data": {
                "name": "Webcam Logitech C920",
                "price": 89.99,
                "stock_quantity": 5,
            },
        },
    ]

    for product in products:
        await send_message(channel, "product", product)
        await asyncio.sleep(0.5)


async def create_orders(channel):
    """Создание 3 заказов"""
    print("Создание заказов")

    orders = [
        {
            "action": "create",
            "data": {
                "user_id": 1,
                "items": [
                    {"product_id": 1, "quantity": 1},
                    {"product_id": 2, "quantity": 2},
                ],
            },
        },
        {
            "action": "create",
            "data": {
                "user_id": 1,
                "items": [
                    {"product_id": 3, "quantity": 1},
                    {"product_id": 4, "quantity": 3},
                ],
            },
        },
        {
            "action": "create",
            "data": {
                "user_id": 1,
                "items": [
                    {"product_id": 2, "quantity": 1},
                    {"product_id": 5, "quantity": 2},
                ],
            },
        },
    ]

    for i, order in enumerate(orders, 1):
        print(f"\nЗаказ #{i}:")
        await send_message(channel, "order", order)
        await asyncio.sleep(1)


async def test_product_operations(channel):
    """Тестирование операций с продуктами"""
    print("Тестирование операций с продуктами")

    print("\n1. Обновление цены продукта #1:")
    await send_message(
        channel, "product", {"action": "update", "data": {"id": 1, "price": 1199.99}}
    )
    await asyncio.sleep(0.5)

    print("\n2. Пометка продукта #5 как закончившегося:")
    await send_message(
        channel, "product", {"action": "mark_out_of_stock", "data": {"id": 5}}
    )
    await asyncio.sleep(0.5)


async def test_order_operations(channel):
    """Тестирование операций с заказами"""
    print("Тестирование операций с заказами")

    print("\n1. Обновление статуса заказа #1 -> processing:")
    await send_message(
        channel,
        "order",
        {"action": "update_status", "data": {"order_id": 1, "status": "processing"}},
    )
    await asyncio.sleep(0.5)

    print("\n2. Обновление статуса заказа #2 -> shipped:")
    await send_message(
        channel,
        "order",
        {"action": "update_status", "data": {"order_id": 2, "status": "shipped"}},
    )
    await asyncio.sleep(0.5)

    print("\n3. Отмена заказа #3 (товары вернутся на склад):")
    await send_message(
        channel,
        "order",
        {"action": "update_status", "data": {"order_id": 3, "status": "cancelled"}},
    )
    await asyncio.sleep(0.5)


async def test_insufficient_stock(channel):
    """Тестирование попытки заказа с недостаточным количеством товара"""
    print("Тестирование: недостаточно товара")

    print("\nПопытка заказать 100 единиц продукта #5 (на складе только 5):")
    await send_message(
        channel,
        "order",
        {
            "action": "create",
            "data": {"user_id": 1, "items": [{"product_id": 5, "quantity": 100}]},
        },
    )
    print("Ожидается ошибка: 'Insufficient stock'")


async def run_rabbitmq_tests():
    """Запуск тестов RabbitMQ"""
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

    print("Подключение к RABBITMQ")
    print(f"URL: {rabbitmq_url}")

    try:
        connection = await connect_robust(rabbitmq_url)
        async with connection:
            channel = await connection.channel()

            await channel.declare_queue("product", durable=True)
            await channel.declare_queue("order", durable=True)

            print("Подключение установлено")
            print("Очереди объявлены")

            await create_products(channel)

            print("\n Ожидание обработки продуктов...")
            await asyncio.sleep(3)

            await create_orders(channel)

            await asyncio.sleep(2)
            await test_product_operations(channel)

            await asyncio.sleep(2)
            await test_order_operations(channel)

            await asyncio.sleep(2)
            await test_insufficient_stock(channel)

            print("Все сообщения отправлены")

            return True

    except Exception as e:
        print(f"\n Ошибка подключения к RabbitMQ: {e}")
        print("\nУбедитесь, что RabbitMQ запущен:")
        print("  docker-compose up -d rabbitmq")
        return False


async def main():
    """Основная функция"""

    print("Комплексное тестирование системы")

    # 1. Проверка API
    api_ok = await check_api_health()
    if not api_ok:
        print("\n Запустите приложение перед выполнением этого скрипта:")
        print(" docker-compose up -d")
        return 1

    # 2. Создание пользователя
    user_id = await create_test_user()
    if not user_id:
        print("\n Не удалось создать тестового пользователя")
        return 1

    # 3. Запуск тестов RabbitMQ
    rabbitmq_ok = await run_rabbitmq_tests()
    if not rabbitmq_ok:
        return 1

    # Финальное сообщение
    print("\n" + "=" * 70)
    print("Тестирование завершено")
    print("=" * 70)
    print(f"\nТестовый пользователь: ID = {user_id}")

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n Прервано пользователем")
        sys.exit(130)
