from aiogram.utils import executor
from courier.telegram_bot.telegram_settings import dp
import logging
from courier.telegram_bot.handlers import start_chat

logging.basicConfig(level=logging.INFO)


async def on_startup(_):
    print('Bot online')


def connector_bot():
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)


if __name__ == '__main__':
    connector_bot()
