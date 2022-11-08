import telebot
from config.settings import TOKEN
from courier.telegram_bot.courier_keyboard import create_main_menu_kb, create_delivered_order

bot = telebot.TeleBot(TOKEN)

main_menu_kb = create_main_menu_kb()



def message_send(courier_telegram, uuid):
    bot.send_message(courier_telegram, 'Клиент отменил заказ. Пожалуйста, вернись в ресторан',
                     reply_markup=[create_delivered_order(uuid)])
    print('send message')


if __name__ == '__main__':
    message_send()
