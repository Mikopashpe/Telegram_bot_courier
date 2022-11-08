import telebot
from config.settings import TOKEN
from courier.models import CourierOrder, CourierInfo
import time
from courier.telegram_bot.courier_keyboard import create_un_allowed_orders_kb, create_main_menu_kb
from django.db.models import Q
from zone.models import Location

main_menu_kb = create_main_menu_kb()
bot = telebot.TeleBot(TOKEN)


def un_allowed_orders_list(location_id):
    """
    Данная функция фильтрует заказы по заданным условиям и возвращает словарь для преобразования его в инлайн-кнопки
    заказов для курьеров.
    """
    return [
        dict(
            restaurant_name=order.order.restaurant.name,
            street=order.order.street,
            house=order.order.house,
            uuid=str(order.order.uuid),
            amount=str(order.order.order_amount),
            entrance=order.order.entrance,
            intercom=order.order.intercom,
            floor=order.order.floor,
            flat=order.order.flat,
            contact_name=order.order.contact_name,
            contact_phone=order.order.contact_phone,
            order_note=order.order.order_note
        ) for order in
        CourierOrder.objects.prefetch_related('order', 'courier').filter(
            Q(order__order_status__in=['created', 'accepted', 'prepared']) &
            Q(order__order_type='delivery') &
            Q(accepted_by_courier=0) &
            Q(order__restaurant__location_id=location_id)
        ).exclude(
            order__order_status__in=['canceled']).all()
    ]


def calling_orders():
    """
    Функция автоматически делает рассылку непринятых заказов по локациям и привязанным к ним курьерам в заданную
    периодичность по id чата. Сообщение обновляется с заданной периодичностью.
    """
    message_dict = {}
    while True:
        time.sleep(20)
        locations = Location.objects.all()
        for location in locations:
            couriers = CourierInfo.objects.filter(Q(location=location) & Q(activity_status=True)).all()
            for courier in couriers:
                if courier.status == True and courier.status_now == False:
                    orders = un_allowed_orders_list(location)
                    kb = create_un_allowed_orders_kb(orders)
                    if courier.telegram in message_dict:
                        bot.delete_message(courier.telegram, message_dict[courier.telegram])
                    message_id = bot.send_message(courier.telegram, text='Непринятые заказы:', reply_markup=[kb])
                    message_dict[courier.telegram] = message_id.message_id


if __name__ == '__main__':
    calling_orders()
