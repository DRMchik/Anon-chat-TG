from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import config as cfg
import logging
import sqlite3

bot = Bot(token=cfg.TOKEN)
dp = Dispatcher(bot)

global con
global curs
con = sqlite3.connect("Anon chat/anon.db")
curs = con.cursor()

def sub(chat_member):
    print(chat_member['status'])

    if chat_member['status'] != 'left':
        return True
    else:
        return False

print('Anon chat is ready!')
logging.basicConfig(level = logging.INFO)

# xD

# Data base
curs.execute("""CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INT,
    active INTEGER DEFAULT (1),
    reg TEXT, 
    status INTEGER
)""")
con.commit()
# user_id - Telegram ID пользователя
# status - статус пользователя: ищет собеседника, не ищет, уже в диологе
# active - доступ к рассылке. 1 - можно; 0 - нельзя
# reg - статус регистрации: yes, no, ban

curs.execute("""CREATE TABLE IF NOT EXISTS queue(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER
)""")
con.commit()

curs.execute("""CREATE TABLE IF NOT EXISTS chats(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    one INTEGER,
    two INTEGER
)""")
con.commit()

# Commands:
# /start
@dp.message_handler(commands = ['start'])
async def start(chat: types.Message):
    if sub(await bot.get_chat_member(chat_id=-1001938263206, user_id=chat.from_user.id)): # Если участник есть в канале
        u_id = chat.from_user.id
        curs.execute("SELECT reg FROM users WHERE user_id = ?", (u_id,))
        r = curs.fetchone()
        if r is None: # если юзер новый
            await chat.answer(f'🎭 Привет, {chat.from_user.username}!')
            await chat.answer('Это анонимный чатик. Здесь ты можешь найти случайного собеседника и пообщаться с ним')
            markup = types.ReplyKeyboardMarkup(one_time_keyboard = True, resize_keyboard = True)
            markup.add(types.KeyboardButton('🔍 Поиск'))
            await chat.answer('Начинай общаться, нажав на кнопку "🔍 Поиск" или прописав команду /search', reply_markup=markup)
            curs.execute("INSERT INTO users(user_id, reg) VALUES(?, ?)", (u_id, 'yes'))
            con.commit()
        else:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard = True, resize_keyboard = True)
            markup.add(types.KeyboardButton('🔍 Поиск'))
            await chat.answer('Хочешь пообщаться? Пропиши команду /search или нажми на кнопочку "🔍 Поиск" и находи собеседника!', reply_markup=markup)
    else: # Если участника нет в канале
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('✅ Наш канал', url = 't.me/Monitoring_channelBot'))
        await chat.answer('❌ Упс... Вам надо зайти в канал бота!', reply_markup = markup)

# /search
@dp.message_handler(commands = ['search'])
async def start(chat: types.Message):
    if sub(await bot.get_chat_member(chat_id=-1001938263206, user_id=chat.from_user.id)): # Если участник есть в канале
        u_id = chat.from_user.id
        curs.execute("SELECT reg FROM users WHERE user_id = ?", (u_id,))
        r = curs.fetchone()
        if r is None: # если юзер новый
            await chat.answer('❌ Пожалуйста, пропишите команду /start , чтобы пользоваться ботом!')
        else:
            curs.execute("SELECT reg FROM users WHERE user_id = ?", (u_id,))
            r = curs.fetchone()[0]
            if r == 'ban':
                await chat.answer('❌ Вы были забанены в нашем боте!')
            else: # если всё оке: основа
                markup = types.ReplyKeyboardMarkup(one_time_keyboard = True, resize_keyboard = True)
                markup.add(types.KeyboardButton('❌ Прекратить поиск'))
                sf = curs.execute("SELECT * FROM queue").fetchmany(1)
                cm = None
                sp = None
                if bool(len(sf)):
                    for row in sf:
                        cm = row[1]
                else:
                    sp = False

                if sp is False:
                    curs.execute("INSERT INTO queue(user_id) VALUES(?)", (u_id,))
                    con.commit()
                    await chat.answer('🔍 Ищем собеседника...', reply_markup=markup)
                else:
                    curs.execute("DELETE FROM queue WHERE user_id = ?", (cm,))
                    con.commit()
                    curs.execute("INSERT INTO chats(one, two) VALUES(?, ?)", (u_id, cm))
                    con.commit()
                    su_msg = '✅ Собеседник найден!\n/stop - завершить беседу (или по кнопке)'
                    markup = types.ReplyKeyboardMarkup(one_time_keyboard = True, resize_keyboard = True)
                    markup.add(types.KeyboardButton('Прекратить беседу'))

                    await bot.send_message(u_id, su_msg, reply_markup=markup)
                    await bot.send_message(cm, su_msg, reply_markup=markup)
    else: # Если участника нет в канале
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('✅ Наш канал', url = 't.me/Monitoring_channelBot'))
        await chat.answer('❌ Упс... Вам надо зайти в канал бота!', reply_markup = markup)

# /stop
@dp.message_handler(commands = ['stop'])
async def start(chat: types.Message):
    if sub(await bot.get_chat_member(chat_id=-1001938263206, user_id=chat.from_user.id)): # Если участник есть в канале
        u_id = chat.from_user.id
        curs.execute("SELECT reg FROM users WHERE user_id = ?", (u_id,))
        r = curs.fetchone()
        if r is None: # если юзер новый
            await chat.answer('❌ Пожалуйста, пропишите команду /start , чтобы пользоваться ботом!')
        else:
            curs.execute("SELECT reg FROM users WHERE user_id = ?", (u_id,))
            r = curs.fetchone()[0]
            if r == 'ban':
                await chat.answer('❌ Вы были забанены в нашем боте!')
            else:
                chat_info = curs.execute("SELECT * FROM chats WHERE one = ?", (u_id,))
                id_chat = 0
                for row in chat_info:
                    id_chat = row[0]
                    chat_info = [row[0], row[2]]
                
                if id_chat == 0:
                    chat_info = curs.execute("SELECT * FROM chats WHERE two = ?", (u_id,))
                    for row in chat_info:
                        id_chat = row[0]
                        chat_info = [row[0], row[1]]
                    if id_chat == 0:
                        await chat.answer('❌ У вас нет никакой беседы')
                    else:
                        markup = types.ReplyKeyboardMarkup(one_time_keyboard = True, resize_keyboard = True)
                        markup.add(types.KeyboardButton('🔍 Поиск'))
                        await chat.answer('✅ Вы закончили беседу!', reply_markup=markup)
                        await bot.send_message(chat_info[1], '❌ Ваш собеседник закончил беседу :(', reply_markup=markup)

                        curs.execute("DELETE FROM chats WHERE id = ?", (chat_info[0],))
                        con.commit()
                else:
                    markup = types.ReplyKeyboardMarkup(one_time_keyboard = True, resize_keyboard = True)
                    markup.add(types.KeyboardButton('🔍 Поиск'))
                    await chat.answer('✅ Вы закончили беседу!', reply_markup=markup)
                    await bot.send_message(chat_info[1], '❌ Ваш собеседник закончил беседу :(', reply_markup=markup)

                    curs.execute("DELETE FROM chats WHERE id = ?", (id_chat,))
                    con.commit()
    else: # Если участника нет в канале
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('✅ Наш канал', url = 't.me/Monitoring_channelBot'))
        await chat.answer('❌ Упс... Вам надо зайти в канал бота!', reply_markup = markup)

@dp.message_handler(content_types='text')
async def msg(chat: types.Message):
    if sub(await bot.get_chat_member(chat_id=-1001938263206, user_id=chat.from_user.id)): # Если участник есть в канале
        u_id = chat.from_user.id
        curs.execute("SELECT reg FROM users WHERE user_id = ?", (u_id,))
        r = curs.fetchone()
        if r is None: # если юзер новый
            await chat.answer('❌ Пожалуйста, пропишите команду /start , чтобы пользоваться ботом!')
        else:
            curs.execute("SELECT reg FROM users WHERE user_id = ?", (u_id,))
            r = curs.fetchone()[0]
            if r == 'ban':
                await chat.answer('❌ Вы были забанены в нашем боте!')
            else:
                msg = chat.text
                if msg == '❌ Прекратить поиск':
                    curs.execute("DELETE FROM queue WHERE user_id = ?", (u_id,))
                    con.commit()
                    markup = types.ReplyKeyboardMarkup(one_time_keyboard = True, resize_keyboard = True)
                    markup.add(types.KeyboardButton('🔍 Поиск'))
                    await chat.answer('❌ Вы прекратили поиск собеседника', reply_markup=markup)

                elif msg == '🔍 Поиск':
                    markup = types.ReplyKeyboardMarkup(one_time_keyboard = True, resize_keyboard = True)
                    markup.add(types.KeyboardButton('❌ Прекратить поиск'))

                    sf = curs.execute("SELECT * FROM queue").fetchmany(1)
                    cm = None
                    sp = None
                    if bool(len(sf)):
                        for row in sf:
                            cm = row[1]
                    else:
                        sp = False

                    if sp is False:
                        curs.execute("INSERT INTO queue(user_id) VALUES(?)", (u_id,))
                        con.commit()
                        await chat.answer('🔍 Ищем собеседника...', reply_markup=markup)
                    else:
                        curs.execute("DELETE FROM queue WHERE user_id = ?", (cm,))
                        con.commit()
                        curs.execute("INSERT INTO chats(one, two) VALUES(?, ?)", (u_id, cm))
                        con.commit()
                        su_msg = '✅ Собеседник найден!\n/stop - завершить беседу (или по кнопке)'
                        markup = types.ReplyKeyboardMarkup(one_time_keyboard = True, resize_keyboard = True)
                        markup.add(types.KeyboardButton('Прекратить беседу'))

                        await bot.send_message(u_id, su_msg, reply_markup=markup)
                        await bot.send_message(cm, su_msg, reply_markup=markup)
                elif msg == 'Прекратить беседу':
                    chat_info = curs.execute("SELECT * FROM chats WHERE one = ?", (u_id,))
                    id_chat = 0
                    for row in chat_info:
                        id_chat = row[0]
                        chat_info = [row[0], row[2]]
                
                    if id_chat == 0:
                        chat_info = curs.execute("SELECT * FROM chats WHERE two = ?", (u_id,))
                        for row in chat_info:
                            id_chat = row[0]
                            chat_info = [row[0], row[1]]
                        if id_chat == 0:
                            await chat.answer('❌ У вас нет никакой беседы')
                        else:
                            markup = types.ReplyKeyboardMarkup(one_time_keyboard = True, resize_keyboard = True)
                            markup.add(types.KeyboardButton('🔍 Поиск'))
                            await chat.answer('✅ Вы закончили беседу!', reply_markup=markup)
                            await bot.send_message(chat_info[1], '❌ Ваш собеседник закончил беседу :(', reply_markup=markup)

                            curs.execute("DELETE FROM chats WHERE id = ?", (chat_info[0],))
                            con.commit()
                    else:
                        markup = types.ReplyKeyboardMarkup(one_time_keyboard = True, resize_keyboard = True)
                        markup.add(types.KeyboardButton('🔍 Поиск'))
                        await chat.answer('✅ Вы закончили беседу!', reply_markup=markup)
                        await bot.send_message(chat_info[1], '❌ Ваш собеседник закончил беседу :(', reply_markup=markup)

                        curs.execute("DELETE FROM chats WHERE id = ?", (id_chat,))
                        con.commit()
                else:
                    chat_info = curs.execute("SELECT * FROM chats WHERE one = ?", (u_id,))
                    id_chat = 0
                    for row in chat_info:
                        id_chat = row[0]
                        chat_info = [row[0], row[2]]
                
                    if id_chat == 0:
                        chat_info = curs.execute("SELECT * FROM chats WHERE two = ?", (u_id,))
                        for row in chat_info:
                            id_chat = row[0]
                            chat_info = [row[0], row[1]]

                    await bot.send_message(chat_info[1], msg)

    else: # Если участника нет в канале
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('✅ Наш канал', url = 't.me/Monitoring_channelBot'))
        await chat.answer('❌ Упс... Вам надо зайти в канал бота!', reply_markup = markup)

executor.start_polling(dp)