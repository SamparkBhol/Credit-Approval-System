from django.core.management.base import BaseCommand
from api.tasks import ingest_data_task

class Command(BaseCommand):
    help = 'Ingests customer and loan data from Excel files into the database via a Celery task.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Dispatching data ingestion task to Celery...'))
        # .delay() is how you send a task to the Celery queue
        ingest_data_task.delay()
        self.stdout.write(self.style.SUCCESS('Task has been sent to the worker. Check worker logs for progress.'))