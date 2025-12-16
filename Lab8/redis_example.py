import redis

# Подключение к Redis
client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# Проверка подключения
try:
    client.ping()
    print("Подключение к Redis успешно")
except redis.ConnectionError:
    print("Ошибка подключения к Redis")
    exit(1)

# Строки
client.set("user:name", "Иван")
name = client.get("user:name")
print(f"Строка user:name = {name}")

client.setex("session:123", 3600, "active")
print(f"Session с TTL = {client.get('session:123')}")

# Счетчики
client.set("counter", 0)
client.incr("counter")
client.incrby("counter", 5)
val = client.decr("counter")
print(f"Counter после операций = {val}")

# Списки
client.delete("tasks")
client.lpush("tasks", "task1", "task2")
client.rpush("tasks", "task3", "task4")
tasks = client.lrange("tasks", 0, -1)
print(f"Список tasks = {tasks}")

first = client.lpop("tasks")
last = client.rpop("tasks")
print(f"Удалены: первый={first}, последний={last}, осталось={client.lrange('tasks', 0, -1)}")

# Множества
client.delete("tags", "languages")
client.sadd("tags", "python", "redis", "database")
client.sadd("languages", "python", "java", "javascript")
print(f"Tags = {client.smembers('tags')}")
print(f"Пересечение tags и languages = {client.sinter('tags', 'languages')}")

# Хеш-таблицы
client.hset("user:1000", mapping={
    "name": "Иван",
    "age": "30",
    "city": "Москва"
})
user_data = client.hgetall("user:1000")
print(f"User 1000 = {user_data}")

# Упорядоченные множества
client.delete("leaderboard")
client.zadd("leaderboard", {
    "player1": 100,
    "player2": 200,
    "player3": 150
})
top = client.zrevrange("leaderboard", 0, 2, withscores=True)
print(f"Топ игроков = {top}")

print("Все операции выполнены успешно")
