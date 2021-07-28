import telebot
from telebot import types
from config import TOKEN

import qrcode  # библиотека для генерации QR-кода для билетов
from random import randint
import os

import requests  # подключение библиотек
from bs4 import BeautifulSoup  # для парсинга


def parse():
    html = requests.get('https://parksirius.ru/').text
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find_all('div', class_='list-item')

    events = []
    for item in items:
        name = item.find('div', class_='col-lg-10 col-md-9 col-sm-12 col-xs-12')
        if name is not None:
            events.append(name.get_text().replace('\n', ''))
    return events


bot = telebot.TeleBot(TOKEN)
data_sirius = ''
index_of_data = 0


@bot.message_handler(commands=['start'])
def command_start(message):
    ID_ = message.from_user.id
    if str(ID_) not in os.listdir('Data_clients'):
        os.mkdir(f'Data_clients//{ID_}')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    main_buttons = [types.KeyboardButton(i) for i in ('Просмотреть мероприятия', 'Записаться на мероприятие', 'Мои мероприятия')]
    markup.add(*main_buttons)
    bot.send_message(message.from_user.id, f'Привет {message.from_user.first_name}', reply_markup=markup)


@bot.message_handler(content_types=['text'])
def bot_message(message: types.Message):
    global data_sirius
    ID_ = message.from_user.id
    data_sirius = parse()
    if message.text == 'Просмотреть мероприятия':
        buttons = [types.InlineKeyboardButton(i[:i.index('|')], callback_data=f'{data_sirius.index(i)}') for i in data_sirius]
        menu = types.InlineKeyboardMarkup(row_width=2).add(*buttons)
        bot.send_message(ID_, 'Список мероприятий: ', reply_markup=menu)

    elif message.text == 'Записаться на мероприятие':
        buttons = [types.InlineKeyboardButton(i[:i.index('|')], callback_data=f'{data_sirius.index(i)}s') for i in data_sirius]
        # добавляем к callback_data букву s, чтобы потом не перепутать это с просмотром
        menu = types.InlineKeyboardMarkup(row_width=2).add(*buttons)
        bot.send_message(ID_, 'Список мероприятий: ', reply_markup=menu)

    elif message.text == 'Мои мероприятия':
        bot.send_message(ID_, 'Ваши мероприятия:')
        for i in os.listdir(f'Data_clients//{ID_}'):
            if 'txt' in i:
                f = open(f'Data_clients//{ID_}//{i}')
                bot.send_message(ID_, f.read())
                f.close()
            else:
                bot.send_photo(ID_, photo=open(f'Data_clients//{ID_}//{i}', 'rb'))

    else:
        bot.send_message(message.from_user.id, 'Неизвестная команда')


def book(message: types.Message):
    global index_of_data
    ID_ = message.from_user.id
    bot.send_message(ID_, 'Ваши билеты:')
    img = qrcode.make(f'{randint(100, 1000)}')
    number = len(os.listdir(f'Data_clients//{ID_}')) + 1
    img.save(f'Data_clients//{ID_}//{number}.png')
    f = open(f'Data_clients//{ID_}//{number + 1}.txt', 'w')
    f.write('Места: ' + message.text + '\n')
    text = data_sirius[index_of_data]
    bot.send_message(ID_, text[:text.index('|')])
    f.write(text[:text.index('|')])
    f.close()
    bot.send_photo(ID_, photo=open(f'Data_clients//{ID_}//{number}.png', 'rb'))


@bot.callback_query_handler(func=lambda call: True)  # работа с кнопками под сообщениями
def callback_inline(call):
    global data_sirius, index_of_data
    try:
        if call.message:
            id_ = call.message.chat.id
            if call.data.isdigit():
                bot.send_message(id_, data_sirius[int(call.data)])
            else:
                index_of_data = int(call.data[:-1])
                msg = bot.send_message(id_, 'Сколько мест вы хотите забронировать?')
                bot.register_next_step_handler(msg, book)

            bot.edit_message_text(chat_id=id_, message_id=call.message.message_id, text=call.message.text, reply_markup=None)
            # удаление использованной кнопки

    except Exception as e:
        print(repr(e))


bot.polling()
