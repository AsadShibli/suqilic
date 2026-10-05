import logging
import threading

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db import close_old_connections

logger = logging.getLogger(__name__)


def dispatch(task, *args) -> None:
    """Queue `task` on Celery when a broker is configured; otherwise run it off the request thread.

    Callers inside a transaction should wrap this in `transaction.on_commit` so the worker sees committed rows.
    """
    if not settings.CELERY_TASK_ALWAYS_EAGER:
        task.delay(*args)
    elif settings.TASKS_THREAD_FALLBACK:
        threading.Thread(target=_run_in_thread, args=(task, args), daemon=True).start()
    else:
        task.apply(args=args, throw=True)


def _run_in_thread(task, args) -> None:
    try:
        task.apply(args=args, throw=True)
    except Exception:  # noqa: BLE001 - background work must never crash the process
        logger.exception("Background task %s failed", task.name)
    finally:
        close_old_connections()


@shared_task(autoretry_for=(OSError,), retry_backoff=True, max_retries=3)
def send_email(subject: str, body: str, to: list[str]) -> None:
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, to)
