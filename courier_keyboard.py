from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def create_auth_kb():
    """
    Клавиатура авторизации курьера. С помощью данной клавиатуры отправляется контакт пользователя с утройства,
    на котором запущен данный бот.
    """
    auth_button = KeyboardButton('🔎Авторизация', request_contact=True)
    auth_kb = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    auth_kb.add(auth_button)
    return auth_kb


def create_location_kb():
    """
    Клавиатура для отправки своего местоположения. В данный момент не используется.
    """
    courier_location_button = KeyboardButton('🗺Отправить свое местоположение', request_location=True)
    courier_loc_kb = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    courier_loc_kb.add(courier_location_button)
    return courier_loc_kb


def create_start_working_kb():
    """
    Клавиатура открытия смены.
    """
    start_working_button = KeyboardButton('👋Открыть смену')
    start_working_kb = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    start_working_kb.add(start_working_button)
    return start_working_kb


def create_main_menu_kb():
    """
    Клавиатура закрытия смены.
    """
    stop_working_button = KeyboardButton('⛔️Закрыть смену')
    main_menu_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    main_menu_kb.insert(stop_working_button)
    return main_menu_kb


def create_confirm_stop_working_kb():
    """
    Клавиатура подтверждения или отмены закрытия смены.
    """
    allow_stop_day = InlineKeyboardButton('Подтвердить', callback_data='allow_stop_day')
    cancel_stop_day = InlineKeyboardButton('Отменить', callback_data='cancel_stop_day')
    confirm_stop_working_kb = InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    confirm_stop_working_kb.insert(allow_stop_day).insert(cancel_stop_day)
    return confirm_stop_working_kb


def create_un_allowed_orders_kb(orders):
    """
    Функция- клавиатура для генерации инлайн-кнопок непринятых заказов.
    """
    orders_keyboard = InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for order in orders:
        button = InlineKeyboardButton(f'{order["restaurant_name"]} => {order["street"]}, {order["house"]}',
                                      callback_data=f'show_order__{str(order["uuid"])}')
        orders_keyboard.add(button)
    return orders_keyboard


def create_allowed_order(uuid):
    """
    Клавиатура для принятия или отмены заказа после предпросмотра.
    """
    allow_order_keyboard = InlineKeyboardMarkup(row_width=2, remove_keyboard=True, one_time_keyboard=True)
    accept_order = InlineKeyboardButton('Подтвердить', callback_data=f'accept_order__{uuid}')
    canceled_order = InlineKeyboardButton('Отменить', callback_data='canceled_order')
    allow_order_keyboard.insert(accept_order).insert(canceled_order)
    return allow_order_keyboard


def create_delivered_order(uuid):
    """
    Клавиатура завершения доставки7
    """
    order_delivered = InlineKeyboardMarkup(one_time_keyboard=True)
    order_is_delivered = InlineKeyboardButton('Заказ доставлен', callback_data=f'order_is_delivered__{uuid}')
    order_delivered.add(order_is_delivered)
    return order_delivered
