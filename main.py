import logging
import json
import re

from aiogram import Bot, Dispatcher
from aiogram.types import *
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor

API_TOKEN = '5804435225:AAGOM6ALUrxj3i4cNFf20U-DQZFeoS-LLSg'

# Configure logging
logging.basicConfig(level=logging.INFO)


# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# Process states 
class ProcessStates(StatesGroup):
    STEP_IIN_Verification = State()
    STEP_New_Phone_Number = State()
    STEP_Region_Choose = State()
    STEP_Area_Choose = State()
    Passive = State()

# Variable initialization for saving IIN of document request in local functions
document_IIN = ""
phone_number = ""
region = ""
area = ""

button1 = KeyboardButton('\u2063🏠 Вернуться в меню', callback_data='start')

get_menu_markup = ReplyKeyboardMarkup(resize_keyboard=True).add(button1)


@dp.message_handler(Command('start'))
async def start_handler(message: Message):
    await message.answer("Теперь Вы можете выбрать нужную опцию из меню или написать Боту вопрос.", reply_markup=get_menu_markup)


@dp.message_handler(lambda message: message.text.startswith('\u2063'))
async def option_handler(query: CallbackQuery):
    book_queue = KeyboardButton('🗓 Бронирование очереди в ЦОН', callback_data='book_queue')
    book_queue_foreign = KeyboardButton('🗓 Бронирование очереди в ЦОН для иностранных граждан', callback_data='book_queue_foreign')
    call_1414 = KeyboardButton('🎧 Связаться с оператором 1414', callback_data='call_1414')
    call_1414_with_social_question = KeyboardButton('📞 Связаться с оператором по вопросам социально-трудовой сферы', callback_data='call_1414_with_social_question')

    temp_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1).add(book_queue, book_queue_foreign, call_1414, call_1414_with_social_question)

    await query.answer("Выберите действие", reply_markup=temp_markup)


@dp.message_handler(lambda message: '🗓 Бронирование' in message.text)
async def button1_handler(query: CallbackQuery):
    link_text = '[здесь](https://egov.kz/cms/ru/services/communications/bron_con)'
    answer_message = f'Вы также можете забронировать очередь в ЦОН {link_text}'
    await query.answer(answer_message, parse_mode=ParseMode.MARKDOWN, reply_markup=get_menu_markup)

    myself = InlineKeyboardButton("На себя", callback_data='myself')
    yourself = InlineKeyboardButton("На другого", callback_data='yourself')

    temp_markup = InlineKeyboardMarkup(resize_keyboard=True, row_width=2).add(myself, yourself)

    await query.answer("На кого хотите забронировать очередь в отдел ЦОН?", reply_markup=temp_markup)


response_yes = InlineKeyboardButton("Да, оставлю", callback_data='use_my_phone_number')
response_no = InlineKeyboardButton("Нет, наберу вручную другой номер", callback_data='use_other_phone_number')

temp_markup = InlineKeyboardMarkup(resize_keyboard=True, row_width=1).add(response_yes, response_no)


# NOTE: After second use of callback there was some trouble with replying to user, query.answer was sending error notification not message, and has no field for markup
@dp.callback_query_handler(text='myself')
async def document_personalization_handler(query: CallbackQuery):
    global phone_number, document_IIN

    with open('data.json', 'r') as file:
        data = json.load(file)

    users_id = data['users']

    for user_id in users_id:
        if user_id[str(query.from_user.id)]:   
            phone_number = user_id[str(query.from_user.id)]['phone']
            document_IIN = user_id[str(query.from_user.id)]["IIN"]
            break
        
    
    alert_text = f"Вы хотите оставить свой номер телефона ({phone_number}), уже зарегистрированный в \"Базе мобильных граждан (БМГ)\", в качестве контактного номера?"

    await bot.send_message(chat_id=query.from_user.id, text=alert_text, reply_markup=temp_markup)
    # await message.answer("hello")

@dp.callback_query_handler(text='yourself')
async def IIN_handler(query: CallbackQuery):
    await bot.send_message(chat_id=query.from_user.id, text="Введите ИИН")
    await ProcessStates.STEP_IIN_Verification.set()


@dp.message_handler(state=ProcessStates.STEP_IIN_Verification)
async def document_personalization_handler(message: Message, state: FSMContext):
    global phone_number, document_IIN

    with open('data.json', 'r') as file:
        data = json.load(file)

    users_id = data['users']
    document_IIN = message.text

    for user_id in users_id:
        if user_id[str(message.from_user.id)]:   
            phone_number = user_id[str(message.from_user.id)]['phone']
            break
        
    
    alert_text = f"Вы хотите оставить свой номер телефона ({phone_number}), уже зарегистрированный в \"Базе мобильных граждан (БМГ)\", в качестве контактного номера?"

    await bot.send_message(chat_id=message.from_user.id, text=alert_text, reply_markup=temp_markup)
    await state.finish()

region_markup = InlineKeyboardMarkup(resize_keyboard=True, row_width=2, 
                                     inline_keyboard=[[
                                         InlineKeyboardButton("Almaty region", callback_data="region_Almaty"),
                                         InlineKeyboardButton("Aqmola region", callback_data="region_Aqmolay"),
                                    ],     
                                    [
                                         InlineKeyboardButton("Almaty", callback_data="city_Almaty"),
                                         InlineKeyboardButton("Astana", callback_data="city_Astana"),
                                     ]])


@dp.callback_query_handler(text='use_my_phone_number')
async def change_phonenumber_handler(query: CallbackQuery):

    alert_text = f"Вы оставили свой номер телефона ({phone_number}) в качестве контактного номера"

    await bot.edit_message_text(chat_id = query.from_user.id, 
                                message_id = query.message.message_id,
                                text=alert_text,
                                reply_markup=None)


    await bot.send_message(chat_id=query.from_user.id, text="Пожалуйста, выберите область из списка:", reply_markup=region_markup)
    await ProcessStates.STEP_Region_Choose.set()


@dp.callback_query_handler(text='use_other_phone_number')
async def change_phonenumber_handler(query: CallbackQuery):

    decline_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Отмена набор номера", callback_data="decline_new_phone"))

    await bot.send_message(chat_id=query.from_user.id, text="Введите Ваш контактный номер телефона в формате 77001234567", reply_markup=decline_markup)
    await ProcessStates.STEP_Region_Choose.set()


@dp.callback_query_handler(text='decline_new_phone')
async def decline_change_phonenumber_handler(query: CallbackQuery):
    await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
    await bot.send_message(chat_id=query.message.chat.id, text="Вы оставили текущий номер", reply_markup=None)

    await bot.send_message(chat_id=query.message.chat.id, text="Пожалуйста, выберите область из списка:", reply_markup=region_markup)
    await ProcessStates.STEP_Region_Choose.set()


@dp.message_handler(regexp=r'^77\d{9}$')
async def changed_phonenumber_handler(message: Message):
    global phone_number

    phone_number = message.text

    alert_text = f"Ваш новый контактный номер: {phone_number}"

    await message.answer(text=alert_text)
    
    await bot.send_message(chat_id=message.from_user.id, text="Пожалуйста, выберите область из списка:", reply_markup=region_markup)
    await ProcessStates.STEP_Region_Choose.set()
    
@dp.message_handler()
async def other_message_handler(message: Message):
    print("I am here")
    # Invalid phone number
    await message.answer(text="Ошибка! Введенный Вами номер телефона не совпадает с форматом. Введите Ваш контактный номер телефона в формате 77001234567")


@dp.callback_query_handler(state=ProcessStates.STEP_Region_Choose)
async def region_handler(query: CallbackQuery):
    global region
    region = str(query.data)

    with open('location.json', 'r') as file:
        data = json.load(file)

    areas = []  
    print(query.data, type(query.data))

    for region_from in data["cities"]:
        if region_from[query.data]:
            areas = region_from[query.data]

    print(areas)

    areas_markup = InlineKeyboardMarkup(resize_keyboard=True, row_width=2)

    for area in areas:
        areas_markup.add(InlineKeyboardButton(area, callback_data=area))

    await bot.send_message(chat_id= query.message.chat.id, text="Пожалуйста, выберите район из списка:", reply_markup=areas_markup)
    await ProcessStates.STEP_Area_Choose.set()

@dp.callback_query_handler(state=ProcessStates.STEP_Area_Choose)
async def region_handler(query: CallbackQuery, state: FSMContext):
    global area
    area = str(query.data)

    data_text = f"Спасибо за заявку, документ в обработке {phone_number}, {document_IIN}, {region}, {area}"

    await bot.send_message(chat_id= query.message.chat.id, text=data_text, reply_markup=get_menu_markup)
    await state.finish()
    # Some API action to send created datas

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
