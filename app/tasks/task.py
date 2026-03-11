import asyncio
import os

from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv
from redis import Redis
import redis_lock

from app.services.image_service import delete_images_without_post
from app.services.tme_message import send_message

load_dotenv()
redis_client = Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    password=os.getenv("REDIS_PASS"),
)
lock_key = "my_task_lock"

celery_app = Celery(
    main="task",
    broker=f"redis://:{os.getenv("REDIS_PASS")}@{os.getenv("REDIS_HOST")}:{os.getenv("REDIS_PORT")}/0",
)


@celery_app.task(
    name="app.tasks.task.delete_images_without_post_task",
    bind=True,
    max_retries=3,
    acks_late=True,
)
def delete_images_without_post_task(self):
    lock = redis_lock.Lock(redis_client, lock_key, expire=60)
    # TODO: что это разобраться
    if not lock.acquire(blocking=False):
        self.retry(countdown=10)
        return
    try:
        result = asyncio.run(delete_images_without_post())
        return result
    except Exception as e:
        # Логируем ошибку и пробуем повторить
        self.retry(exc=e, countdown=300)


@celery_app.task(
    name="app.tasks.task.send_message_task",
    bind=True,
    max_retries=3,
    acks_late=True,
)
def send_message_task(self, content):
    lock = redis_lock.Lock(redis_client, lock_key, expire=60)
    if not lock.acquire(blocking=False):
        self.retry(countdown=10)
        return
    try:
        result = asyncio.run(send_message(content))
        return f"success message_id = {result}"
    except Exception as e:
        # Логируем ошибку и пробуем повторить
        self.retry(exc=e, countdown=300)
        self.retry(exc=e, countdown=300)
    finally:
        try:
            lock.release()
        except Exception:
            pass


@celery_app.task(
    name="app.tasks.task.send_message_task",
    bind=True,
    max_retries=3,
    acks_late=True,
)
def send_message_task(self, content):
    lock = redis_lock.Lock(redis_client, lock_key, expire=60)
    if not lock.acquire(blocking=False):
        self.retry(countdown=10)
        return
    try:
        result = asyncio.run(send_message(content))
        return f"success message_id = {result}"
    except Exception as e:
        # Логируем ошибку и пробуем повторить
        self.retry(exc=e, countdown=300)
    finally:
        try:
            lock.release()
        except Exception:
            pass


celery_app.conf.timezone = "Europe/Moscow"
celery_app.conf.beat_schedule = {
    "task-name": {
        "task": "app.tasks.task.delete_images_without_post_task",
        "schedule": crontab(hour=2, minute=00),  # Раз в день в 2.00
    },
}
