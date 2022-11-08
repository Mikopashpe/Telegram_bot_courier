import re

from django.db import transaction
import aiogram
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from aiogram import types
from aiogram.types import ContentType, update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, message
from order.models import Order
from courier.models import CourierOrder
from .telegram_settings import dp, bot
from .helpers import search_courier_by_phone, search_courier_by_telegram_id, \
    search_courier_by_telegram_id_, on_delivery_by_telegram_id, end_delivery_by_telegram_id_, writing_telegram_id
from .courier_keyboard import create_auth_kb, create_main_menu_kb, create_start_working_kb, \
    create_confirm_stop_working_kb, create_allowed_order, create_delivered_order
from ..models import CourierInfo

auth_kb = create_auth_kb()
main_menu_kb = create_main_menu_kb()
start_working_kb = create_start_working_kb()
confirm_stop_working_kb = create_confirm_stop_working_kb()


@dp.message_handler(commands=['help'])
async def helper(message: types.Message):
    """
    Данная функция служит мануалом по использованию команд бота и вызывается путем ввода команды в поле ввода после слэша
    """
    await bot.send_message(message.from_user.id,
                           '''
                           Привет!🙂\n
                           Я твой помощник.\n
                           Давай расскажу тебе, что к чему 😎\n
                           Для начала тебе нужно пройти\n 🔎Авторизацию.\nСледуй указаниям на кнопке.\n
                           👋 Открыть смену- начинает твой рабочий день\nПосле открытия смены я отправлю тебе заказы - здесь ты увидишь 
                           непринятые на текущий момент заказы и сможешь выбрать один из них\n
                           ⛔️ Закрыть смену - сообщает, что ты закончил работать\nЧтобы снова начать работать, нажми\n👋 Открыть смену''')


@dp.message_handler(commands=['start'])
async def start_chat(message: types.Message):
    """
    Данная функция активирует бота для дальнейшего взаимодействия. Может отсутствовать ввиду встроенной кнопки "Начать"
    на некоторых устойствах.
    """
    await message.reply(text='Рады приветствовать тебя! Пожалуйста, авторизуйся ))',
                        reply_markup=auth_kb)


@dp.message_handler(content_types=ContentType.CONTACT)
async def courier_phone_auth(message: types.contact):
    """
    Данная функция запрашивает контакт курьера, который автоматически формируется через кнопку. Затем идет поиск по базе
    данного курьера. При наличии записи такого номера телефона происходит проверка статуса активности курьера и идет
    запись id чата в соответствующее поле в базе данных. При прохождении проверки пользователь получает сообщение
    'Вы авторизованы ✅' и может продолжать взаимодействие с ботом.
    """
    courier_phone = await search_courier_by_phone(message['contact']['phone_number'])
    if courier_phone['phone'] == message.contact.phone_number:
        ct = courier_phone['phone']
        telegram_id_recieve = str(message.from_user.id)
        await bot.send_message(message.from_user.id, 'Вы авторизованы ✅', reply_markup=start_working_kb)
        await writing_telegram_id(ct, telegram_id_recieve)
    else:
        await bot.send_message(message.from_user.id, 'Вы не прошли авторизацию ⛔️')


@dp.message_handler(regexp='Открыть смену')
async def start_day(message: types.Message):
    """
    Данная функция меняет булево значение поля курьера "Работает сегодня" на True. При открытии смены на id чата курьера
    с учетом его локации начинается рассылка с непринятыми на текущий момент заказами.
    """
    on_working = await search_courier_by_telegram_id(message['from']['id'])
    await bot.send_message(message.from_user.id, text='Ваша смена начинается. Приступим!', reply_markup=main_menu_kb)


@dp.message_handler(regexp='Закрыть смену')
async def stop_day(message: types.Message):
    """
    Данная функция меняет булево значение поля курьера "Работает сегодня" на False. При закрытии смены на id чата
    курьера прекращается рассылка непринятых заказов до следующего открытия смены. Действие закрытия смены необходимо
    подтвердить или отменить последующими командами 'Подтвердить' и 'Отменить'.
    """
    await bot.send_message(message.from_user.id, text='Пожалуйста, подтвердите окончание смены',
                           reply_markup=confirm_stop_working_kb)


@dp.message_handler(commands=['Подтвердить'])
async def register_handlers_courier(message: types.Message):
    await message.reply('')


@dp.callback_query_handler(lambda c: c.data == 'allow_stop_day')
async def process_callback_button1(callback_query: types.CallbackQuery):
    """
    Данная функция меняет булево значение поля курьера "Работает сегодня" на False.
    """
    on_working = await search_courier_by_telegram_id_(callback_query['from']['id'])
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Ваша смена окончена!', reply_markup=start_working_kb)
    await callback_query.message.delete()


@dp.message_handler(commands=['Отменить'])
async def register_handlers_courier(message: types.Message):
    await message.reply('')


@dp.callback_query_handler(lambda c: c.data == 'cancel_stop_day')
async def process_callback_button1(callback_query: types.CallbackQuery):
    """
    Данная функция отменяет изменение статуса курьера и удаляет сообщение о закрытии смены вместе с клавиатурой.
    После нажатия кнопки 'Отменить' работа с ботом продолжается до закрытия смены курьером.
    """
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.delete()


with transaction.atomic():
    @dp.message_handler(commands=['Подтвердить'])
    async def register_handlers_courier(message: types.Message):
        """
        Данная функция срабатывает при подтверждении заказа из автоматической рассылки. Происходит смена статуса курьера
        и бронь выбранного заказа за ним. На экран выводится подробная информация о заказе. Рассылка на период доставки
        данного заказа прекращается. При одновременном выборе одного и того же заказа несколькими курьерами
        заказ будет передан курьеру, раньше всех подтвердившему выбор данного заказа. Остальным курьерам придет отбивка
        о недоступности данного заказа.
        """
        await message.reply('')


@dp.callback_query_handler(
    lambda c: re.match(
        r'accept_order__[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}$', c.data))
async def process_status_change(callback_query: types.CallbackQuery):
    @sync_to_async
    def get_uuid_for_order(uuid, chat_id):
        try:
            with transaction.atomic():
                search_order = Order.objects.filter(uuid=uuid).get()
                search_courier = CourierOrder.objects.filter(order_id=search_order).get()
                if not search_courier.accepted_by_courier:
                    search_courier.accepted_by_courier = True
                    search_courier.save()
                    courier = CourierInfo.objects.filter(telegram=chat_id).first()
                    search_courier.courier = courier
                    search_courier.save()
                else:
                    return

        except TypeError:
            raise TypeError

        return dict(restaurant_name=search_courier.order.restaurant.name,
                    street=search_courier.order.street,
                    house=search_courier.order.house,
                    uuid=str(search_courier.order.uuid),
                    amount=str(search_courier.order.order_amount),
                    entrance=search_courier.order.entrance,
                    intercom=search_courier.order.intercom,
                    floor=search_courier.order.floor,
                    flat=search_courier.order.flat,
                    contact_name=search_courier.order.contact_name,
                    contact_phone=search_courier.order.contact_phone,
                    order_note=search_courier.order.order_note)

    change_status = await get_uuid_for_order(callback_query.data.split('__')[1], callback_query['from']['id'])
    if not change_status:
        await bot.send_message(callback_query.from_user.id, text='Упс... Этот заказ уже кто-то взял',
                               reply_markup=main_menu_kb)
        # await callback_query.message.delete()
        return
    text = f'<b>Заказ из ресторана:</b> {change_status["restaurant_name"]}\n<b>Доставить по адресу:</b>\nул. {change_status["street"]}, д. ' \
           f'{change_status["house"]}, п. {change_status["entrance"]}, д. {change_status["intercom"]}, эт. {change_status["floor"]}, кв. ' \
           f'{change_status["flat"]}\n<b>Контактное лицо:</b>\n{change_status["contact_name"]}\n<b>тел</b>. {change_status["contact_phone"]}\n' \
           f'<b>Комментарий к заказу:</b>\n{change_status["order_note"]}'
    on_working = await on_delivery_by_telegram_id(callback_query['from']['id'])
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, text=text, parse_mode='html',
                           reply_markup=create_delivered_order(change_status["uuid"]))
    # await callback_query.message.delete()


@dp.message_handler(commands=['Отменить'])
async def register_handlers_courier(message: types.Message):
    await message.reply('')


@dp.callback_query_handler(lambda c: c.data == 'canceled_order')
async def cancel_allow_order(callback_query: types.CallbackQuery):
    """
    Данная функция отменяет предварительный выбор заказа и "возвращает" в меню - рассылка непринятых заказов продолжается.
    """
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.delete()
    await bot.send_message(callback_query.from_user.id, text='Возвращаю вас в меню', reply_markup=main_menu_kb)



@dp.message_handler(regexp='Заказ доставлен')
async def delivery_order(message: types.Message):
    """
    Данная функция меняет статус курьера для продолжения рассылки о непринятых заказах. Меняется статус заказа на
    "Доставлен"
    """
    await message.reply('')


@dp.callback_query_handler(
    lambda c: re.match(
        r'order_is_delivered__[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}$',
        c.data))
async def process_order_status_change(callback_query: types.CallbackQuery):
    @sync_to_async
    def get_uuid_for_changing_order(uuid):
        search_order_for_status = Order.objects.filter(uuid=uuid).get()
        search_order_for_status.order_status = 'delivered'
        search_order_for_status.save()

    change_status = await get_uuid_for_changing_order(callback_query.data.split('__')[1])
    on_working = await end_delivery_by_telegram_id_(callback_query['from']['id'])
    text = 'Заказ доставлен!'
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, text=text, reply_markup=main_menu_kb)


@dp.callback_query_handler(
    lambda c: re.match(
        r'show_order__[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}$',
        c.data))
async def process_order(callback_query: types.CallbackQuery):
    """
    Данная функция выводит на экран курьера по запросу более подробную информацию о заказе.
    """

    @sync_to_async
    def get_order_by_uuid(uuid):
        try:
            search_order = Order.objects.filter(uuid=uuid).get()
            search_courier = CourierInfo.objects.filter(location=search_order.restaurant.location.id).first()

        except ObjectDoesNotExist as exc:
            raise ObjectDoesNotExist
        if search_courier.location.id == search_order.restaurant.location.id:
            return dict(restaurant_name=search_order.restaurant.name,
                        street=search_order.street,
                        house=search_order.house,
                        uuid=str(search_order.uuid),
                        amount=str(search_order.order_amount),
                        entrance=search_order.entrance,
                        intercom=search_order.intercom,
                        floor=search_order.floor,
                        flat=search_order.flat,
                        contact_name=search_order.contact_name,
                        contact_phone=search_order.contact_phone,
                        order_note=search_order.order_note)

    order = await get_order_by_uuid(callback_query.data.split('__')[1])
    text = f'<b>Заказ из ресторана:</b> {order["restaurant_name"]}\n<b>Доставить по адресу:</b>\nул. {order["street"]}, д. ' \
           f'{order["house"]}, п. {order["entrance"]}, д. {order["intercom"]}, эт. {order["floor"]}, кв. ' \
           f'{order["flat"]}\n<b>Контактное лицо:</b>\n{order["contact_name"]}\n<b>тел</b>. {order["contact_phone"]}\n' \
           f'<b>Комментарий к заказу:</b>\n{order["order_note"]}'
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, text='Выберите опцию', reply_markup=ReplyKeyboardRemove())
    # await bot.send_message(callback_query.from_user.id, text='Выберите опцию', reply_markup=create_allowed_order())
    await bot.send_message(callback_query.from_user.id, text=text, parse_mode='html',
                           reply_markup=create_allowed_order(order['uuid']))
    # await callback_query.message.delete()
