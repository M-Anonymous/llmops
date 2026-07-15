from uuid import UUID

from celery import shared_task


@shared_task
def demo_task(uuid: UUID) -> str:
    print(uuid)
    return str(uuid)