from courier.call_about_unallowed_orders import calling_orders
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'command to launch the bot in the telegram'

    def handle(self, *args, **options):
        calling_orders()
