from courier.orders_bot import orders_list
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'command to launch the bot in the telegram'

    def handle(*args, **options):
        orders_list()
