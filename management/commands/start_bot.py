from django.core.management.base import BaseCommand
from courier.telegram_bot.bot_telegram import *


class Command(BaseCommand):
    help = 'command to launch the bot in the telegram'

    def handle(self, *args, **options):
        connector_bot()





