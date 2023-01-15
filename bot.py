import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import KeyboardButton as kb
from aiogram.types import InlineKeyboardButton as ikb
from aiogram.types import InputFile
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
import requests as rq
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from random import choice
import random
import datetime as dt
import os
import aiogram.utils.markdown as md
import copy
import psycopg2
import aioschedule as sch
import asyncio as aio
import configparser

cp = configparser.ConfigParser()
cp.read("config.ini")
bot = Bot(token=cp["Bot"]["TOKEN"], parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

conn = psycopg2.connect(user=cp["DB"]["user"], password=cp["DB"]["pwd"], host=cp["DB"]["host"], port=cp["DB"]["port"], database=cp["DB"]["db"])

class QuestState(StatesGroup):
    answer = State()

class SendLetterState(StatesGroup):
    ltr_text = State()

class CongratState(StatesGroup):
    wait_dt = State()
    wait_msg = State()

parties = [
    [6, [2, "Твоё признание", "ты призналась мне, что я тебе нравлюсь"], [2, "Первые обнимашки", "мы впервые по-настоящему обнимались"]],
    [9, [2, "Официальное начало отношений", "мы официально начали встречаться"], [4, "Первое свидание - поход в кино", "у нас состоялось первое свидание в привычном смысле этого слова - мы сходили в кино"]],
    [10, [4, "Твоё второе признание", "ты сказала, что любишь меня"]],
    [13, [1, "Начало нашего общения", "мы с тобой начали переписываться"], [2, "Первый поцелуй", "мы впервые поцеловались"]],
    [16, [1, "Твой день рождения", "тебе исполнилось 18 лет"]],
    [17, [2, "Моё второе признание", "я сказал, что люблю тебя"]],
    [25, [2, "Мой день рождения", "мне исполнилось 16 лет"]],
    [26, [1, "Первая личная встреча", "мы впервые лично встретились"], [3, "Знакомство с моими родителями", "ты познакомилась и лично встретилась с моими родителями"]],
    [30, [1, "Моё признание", "я признался, что ты мне нравишься"]]
]
monthes = [
    "null",
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря"
]

@dp.message_handler(commands=['start'])
async def start_handler(msg: types.Message, state: FSMContext):
    await msg.answer("Привет! Этот бот я создал лишь для нас с тобой, любимая ❤️")
    await msg.answer("Он может отправить тебе одно из наших фото из нашей коллекции по команде /getphoto 📷")
    await msg.answer("Отправляя боту фото (только отправляй по одной, пожалуйста) ты можешь пополнить коллекцию своей фотографией 😊")
    await msg.answer("Команда /ourmusic отправит тебе случайную песен из наших с тобой 🎵🎵🎵")
    await msg.answer("Также я составил календарь наших с тобой праздников, ты можешь получить его в виде списка наших дат командой /calend, либо посмотреть, какой ближайший наш праздник командой /party 🙃")
    await msg.answer("Ещё ты можешь написать поздравление к какому-то празднику, используя команду /congratulate")
    await msg.answer('Ещё я сделал прикольную штуку, которую назвал "любовные письма" 💌 \nЧтобы написать мне письмо (ну или записочку 🙃) нужно ввести команду /send_letter \nЧтобы прочитать накопившиеся письма от меня, напиши /take_letter')
    await msg.answer("Но чтобы ПОЛЬзовться всем этим, нужно подтвердить, что это действительно ты 😏 \nНичего сложного в этом нет, надо просто ответить на вопрос, ответ на который знаем только мы с тобой 😊")
    quests = (
        ("Какого числа у нас самый большой наш праздник?", ["9"],"Именно число, без месяца, просто цифра, попробуй ещё раз 😉"),
        ("Где мы встретились в самый-самый первый раз?", ["на роднике", "родник", "на слёте", "слёт", "на слете", "слет", "ангар", "в ангаре", "петропавловка", "в петропавловке"],"Попробуй ещё, одним-двумя словами 😉"),
        ("Название нашей с тобой любимой песни", ["молитва"], "Всего одним словом, только название, постарайся ещё 😉"),
        ("Как меня зовут?", ["ванечка"], "Дам подсказку, как меня зовёшь ТЫ 😊"),
        ("На какой улице я живу?", ["инструментальная", "зелёная", "зеленая", "на инструментальной", "на зеленой", "на зелёной"], "Название улицы в именительном падеже! Вспомни ЕГЭ по русскому 😆"),
        ("Что мы с тобой считали, когда сильно скучали?", ['часы', 'часы до встречи'], 'ПОДСКАЗКА: чаще всего в эти моменты я был далеко 🙃')
    )
    question = choice(quests)
    await msg.answer(question[0])
    async with state.proxy() as data:
        data['right_answers'] = question[1]
        data['pod'] = question[2]
    await QuestState.answer.set()

@dp.message_handler(state=QuestState.answer)
async def quest_answer_handler(msg: types.Message, state: FSMContext):
    async with state.proxy() as data:
        right_answers = data['right_answers']
        pod = data['pod']
    if msg.text.lower() in right_answers:
        await msg.answer("Молодец, такое невозможно забыть 😊😉")
        await state.finish()
        return
    else:
        await msg.answer(pod)
        await QuestState.answer.set()
        return

@dp.message_handler(commands=["getphoto"])
async def getphoto_handler(msg: types.Message):
    cur = conn.cursor()
    cur.execute("SELECT file_id FROM files_id WHERE split_part(filename, '.', 2) != 'mp3' ORDER BY random() LIMIT 1;")
    try:
        await msg.answer_photo(cur.fetchone()[0])
    except: 
        print("No files with this File ID found!")
        files = os.listdir("./photo")
        file_name = random.choice(files)
        img = InputFile("photo/"+file_name)
        mes = await msg.answer_photo(img)
        cur.execute(f"INSERT INTO files_id (file_id, filename) VALUES ('{mes.photo[-1]}', '{file_name}');")
        conn.commit()
    finally:
        cur.close()

@dp.message_handler(content_types=['photo'])
async def upload_handler(msg: types.Message):
    photo_path = str(dt.datetime.now().strftime("%Y-%m-%d %H-%M-%S"))+".jpg"
    await msg.photo[-1].download(destination_file="photo/"+photo_path)
    cur = conn.cursor()
    cur.execute(f"INSERT INTO files_id (file_id, filename) VALUES ('{msg.photo[-1]}', '{photo_path}');")
    conn.commit()
    await msg.answer("Твоё фото успешно загружено 😉")

@dp.message_handler(commands=["ourmusic"])
async def ourmusic_handler(msg: types.Message):
    cur = conn.cursor()
    cur.execute("SELECT file_id FROM files_id WHERE split_part(filename, '.', 2) = 'mp3' ORDER BY random() LIMIT 1;")
    try:
        await msg.answer_audio(cur.fetchone()[0])
    except: 
        print("No files with this File ID found!")
        files = os.listdir("music")
        file_name = random.choice(files)
        msc = InputFile("music/"+file_name)
        mes = await msg.answer_audio(msc)
        cur.execute(f"INSERT INTO files_id (file_id, filename) VALUES ('{mes.audio}', '{file_name}');")
        conn.commit()
    finally:
        cur.close()

@dp.message_handler(commands=["calend"])
async def calend_handler(msg: types.Message):
    await msg.answer("<b><u>Календарь наших с тобой праздников)</u></b>\n<b>13 января</b> - начало нашего общения\n<b>16 января</b> - твой день рождения\n<b>26 января</b> - первая личная встреча\n<b>30 января</b> - признание с моей стороны\n<b>6 февраля</b> - твоё признание, а также обнимашки \n<b>9 февраля</b> - официально начали встречаться\n<b>13 февраля</b> - первый поцелуй\n<b>17 февраля</b> - моё второе признание\n<b>25 февраля</b> - мой день рождения\n<b>26 марта</b> - знакомство с моими родителями\n<b>9 апреля</b> - первое нормальное свидание в кино\n<b>10 апреля</b> - твоё второе признание")

@dp.message_handler(commands=["party"])
async def party_handler(msg: types.Message):
    cur = [int(dt.datetime.now().strftime("%-d")), int(dt.datetime.now().strftime("%-m")), int(dt.datetime.now().strftime("%Y"))]
    party = []
    next_party = []
    j = False
    for i in parties:
        if j:
            next_party = copy.deepcopy(i)
            break
        if cur[0] < i[0]:
            party = copy.deepcopy(i)
            break
        if cur[0] == i[0]:
            j =  True
            party = copy.deepcopy(i)
    if len(party) == 0:
        party = parties[0]
        if cur[1] == 12:
            cur[1] = 1
            cur[2] += 1
        else:    
            cur[1] += 1
    if len(next_party) == 0:
        if len(party) == 2:
            n = (cur[2] - 2022) * 12 + (cur[1] - party[1][0])
            await msg.answer("Следующий наш с тобой праздник будет " + str(party[0]) + " " + monthes[cur[1]] + " - <b><i>" + party[1][1] + "</i></b>\nВ этом месяце будет уже " + str(n) + " месяцев, как " + party[1][2])
        elif len(party) == 3:
            n1 = (cur[2] - 2022) * 12 + (cur[1] - party[1][0])
            n2 = (cur[2] - 2022) * 12 + (cur[1] - party[2][0])
            await msg.answer("Следующие наши с тобой праздники будут " + str(party[0]) + " " + monthes[cur[1]] + ": \n<b><i>" + party[1][1] + "</i></b>. В этом месяце будет уже " + str(n1) + " месяцев, как " + party[1][2] + "\n<b><i>" + party[2][1] + "</i></b>. В этом месяце будет уже " + str(n2) + " месяцев, как " + party[2][2])
    else:
        if len(party) == 2:
            n = (cur[2] - 2022) * 12 + (cur[1] - party[1][0])
            await msg.answer("Сегодня мы с тобой отмечаем <b><i>" + party[1][1] + "</i></b>\nПрошло уже " + str(n) + " месяцев, как " + party[1][2])
        elif len(party) == 3:
            n1 = (cur[2] - 2022) * 12 + (cur[1] - party[1][0])
            n2 = (cur[2] - 2022) * 12 + (cur[1] - party[2][0])
            await msg.answer("Сегодня мы с тобой отмечаем <b><i>" + party[1][1] + "</i></b> и <b><i>" + party[2][1] + "</i></b>\nПрошло уже " + str(n1) + " месяцев, как " + party[1][2] + " и " + str(n2) + " месяцев, как " + party[2][2])
        if len(next_party) == 2:
            n = (cur[2] - 2022) * 12 + (cur[1] - next_party[1][0])
            await msg.answer("Следующий наш с тобой праздник будет " + str(next_party[0]) + " " + monthes[cur[1]] + " - <b><i>" + next_party[1][1] + "</i></b>\nВ этом месяце будет уже " + str(n) + " месяцев, как " + next_party[1][2])
        elif len(next_party) == 3:
            n1 = (cur[2] - 2022) * 12 + (cur[1] - next_party[1][0])
            n2 = (cur[2] - 2022) * 12 + (cur[1] - next_party[2][0])
            await msg.answer("Следующие наши с тобой праздники будут " + str(next_party[0]) + " " + monthes[cur[1]] + ": \n<b><i>" + next_party[1][1] + "</i></b>. В этом месяце будет уже " + str(n1) + " месяцев, как " + next_party[1][2] + "\n<b><i>" + next_party[2][1] + "</i></b>. В этом месяце будет уже " + str(n2) + " месяцев, как " + next_party[2][2])

@dp.message_handler(commands=["send_letter"])
async def send_letter_handler(msg: types.Message):
    keyb = types.InlineKeyboardMarkup().add(ikb("Нихачу", callback_data="cancel_send"))
    await msg.answer('Если хочешь оставить любовную записку для меня, просто напиши её и отправь мне, а если передумала, нажми на кнопку 😆', reply_markup=keyb)
    await SendLetterState.ltr_text.set()

@dp.callback_query_handler(text="cancel_send", state=SendLetterState.ltr_text)
async def cancel_send_handler(clbck: types.CallbackQuery, state: FSMContext):
    await clbck.message.answer("Ну ладно, можешь дальеш наслаждаться функционалом бота, а если захочешь вернуться к написанию записочки, просто отправь команду /send_letter 😉")
    await state.finish()

@dp.message_handler(state=SendLetterState.ltr_text)
async def sending_letter(msg: types.Message, state: FSMContext):
    cur = conn.cursor()
    cur.execute("INSERT INTO entries (username, msg, time) VALUES ('%s', '%s', '%s');" % (msg.from_user.full_name, msg.text, str(dt.datetime.now())))
    cur.close()
    conn.commit()
    await msg.answer("Твоя записочка сохранена, я увижу её когда загляну сюда 😉")
    await state.finish()
    if msg.from_user.id == cp["Bot"]["POLINA_ID"]:
        cp.set("Bot", "ME_UNREAD", "True")
        with open("config.ini", "w+") as file:
            cp.write(file)
    elif msg.from_user.id == cp["Bot"]["ME_ID"]:
        cp.set("Bot", "POLINA_UNREAD", "True")
        with open("config.ini", "w+") as file:
            cp.write(file)

num = 10

@dp.message_handler(commands=["take_letter"])
async def take_letter_handler(msg: types.Message):
    cur = conn.cursor()
    cur.execute("SELECT * FROM entries ORDER BY id DESC LIMIT 11;")
    global num
    num = 10
    res = cur.fetchall()
    if len(res) == 11:
        flag = True
    else:
        flag = False
    if len(res) == 11:
        res = res[:-1]
    for i in res:
        await msg.answer("От: %s\nКогда: %s\nЗаписка: %s" % (i[1], i[3], i[2]))
    if flag:
        keyb = types.InlineKeyboardMarkup().add(ikb("Предыдущие записки", callback_data="list_10"))
        await msg.answer("Нажми на кнопку если хочешь посмотреть предыдущие 10 записок", reply_markup=keyb)
    cur.close()
    if msg.from_user.id == int(cp["Bot"]["POLINA_ID"]):
        cp.set("Bot", "POLINA_UNREAD", "False")
        with open("config.ini", "w+") as file:
            cp.write(file)
    elif msg.from_user.id == int(cp["Bot"]["ME_ID"]):
        print("Ivan readed messages")
        cp.set("Bot", "ME_UNREAD", "False")
        with open("config.ini", "w+") as file:
            cp.write(file)

@dp.callback_query_handler(Text(startswith="list"))
async def take_more(clbck: types.CallbackQuery):
    cur = conn.cursor()
    global num
    cur.execute("SELECT * FROM entries ORDER BY id DESC LIMIT 11 OFFSET %d;" % num)
    res = cur.fetchall()
    num += 10
    if len(res) == 11:
        flag = True
    else:
        flag = False
    if len(res) == 11:
        res = res[:-1]
    for i in res:
        await clbck.message.answer("От: %s\nКогда: %s\nЗаписка: %s" % (i[1], i[3], i[2]))
    if flag:
        keyb = types.InlineKeyboardMarkup().add(ikb("Предыдущие записки", callback_data="list_"+str(num)))
        await clbck.message.answer("Нажми на кнопку если хочешь посмотреть предыдущие 10 записок", reply_markup=keyb)
    cur.close()

@dp.message_handler(commands=['congratulate'])
async def congrat_yandler(msg: types.Message):
    await msg.answer("Для начала выбери дату, когда мне надо показать это поздравление\nДля этого напиши дату и время в формате 'день-месяц-год час:минута'")
    await CongratState.wait_dt.set()

@dp.message_handler(state=CongratState.wait_dt)
async def congrat_date(msg: types.Message, state: FSMContext):
    try:
        congrat_dt = dt.datetime.strptime(msg.text, "%d-%m-%Y %H:%M")
    except Exception as e:
        await msg.answer("К сожалению введённая дата не подходит, скорее всего нерпавильный формат, попробуй снова")
        print(e)
    else:
        await state.update_data(congrat_time=congrat_dt)
        await CongratState.wait_msg.set()
        await msg.answer("А теперь отправь текст поздавления")

new_congr = True

@dp.message_handler(state=CongratState.wait_msg)
async def congrat_finish(msg: types.Message, state: FSMContext):
    async with state.proxy() as data:
        congr_date = data['congrat_time']
    if msg.from_user.id == (cp['Bot']['polina_id']):
        to_id = cp['Bot']['me_id']
    elif msg.from_user.id == int(cp['Bot']['me_id']):
        to_id = cp['Bot']['polina_id']
    cur = conn.cursor()
    cur.execute("INSERT INTO congratulations (to_id, text, date) VALUES ('%s', '%s', '%s');" % (to_id, msg.text, congr_date))
    await msg.answer("Твоё поздравление добавлено и будет показано)")
    cur.close()
    conn.commit()
    global new_congr
    new_congr = True
    await state.finish()

async def congratulate():
    global new_congr
    while True:
        if new_congr:
            cur = conn.cursor()
            cur.execute("SELECT * FROM congratulations;")
            res = cur.fetchall()
            cur.close()
            new_congr = False
        for j in res:
            if dt.datetime.now().replace(second=0, microsecond=0) == j[3]:
                print("Hoorah!")
                await bot.send_message(j[1], j[2])
                cur = conn.cursor()
                cur.execute("DELETE FROM congratulations WHERE id=%d" % j[0])
                new_congr = True
        await aio.sleep(10)

async def notify():
    msg_text = "Загляни в записочки, кажется там есть кое-что для тебя 🙃"
    if cp.getboolean('Bot', 'ME_UNREAD'):
        await bot.send_message(cp["Bot"]["ME_ID"], msg_text)
    if cp.getboolean('Bot', 'POLINA_UNREAD'):
        await bot.send_message(cp["Bot"]["POLINA_ID"], msg_text)

@dp.message_handler(commands=['sendstick'])
async def send_sticker(msg: types.Message):
    await msg.answer_sticker("❤️")

async def happy_party():
    for i in parties:
        if int(dt.datetime.now().strftime("%-d")) == 16:
            await bot.send_message(cp["Bot"]["POLINA_ID"], f"Поздравляю, сегодня у тебя праздник - <b>День Рождения</b>! 🎉\nСегодня мы с тобой отмечаем твоё <i>девятнадцатилетие</i> 🎉🎉🎉\nС днём рождения, любимая ❤️❤️❤️")
            
        if int(dt.datetime.now().strftime("%-d")) == i[0]:
            if len(i) == 2:
                n = (int(dt.datetime.now().strftime("%Y")) - 2022) * 12 + (int(dt.datetime.now().strftime("%-m")) - i[1][0])
                await bot.send_message(cp["Bot"]["POLINA_ID"], f"Поздравляю, сегодня у нас с тобой праздник - <b>{i[1][1]}</b>! 🎉\nСегодня мы с тобой отмечаем {n} месяцев с дня, когда <i>{i[1][2]}</i> 🎉🎉🎉")
                await bot.send_message(cp["Bot"]["ME_ID"], f"Поздравляю, сегодня у нас с тобой праздник - <b>{i[1][1]}</b>! 🎉\nСегодня мы с тобой отмечаем {n} месяцев с дня, когда <i>{i[1][2]}</i> 🎉🎉🎉")
            elif len(i) == 3:
                n1 = (int(dt.datetime.now().strftime("%Y")) - 2022) * 12 + (int(dt.datetime.now().strftime("%-m")) - i[1][0])
                n2 = (int(dt.datetime.now().strftime("%Y")) - 2022) * 12 + (int(dt.datetime.now().strftime("%-m")) - i[2][0])
                await bot.send_message(cp["Bot"]["POLINA_ID"], f"Поздравляю, сегодня у нас с тобой аж ДВА праздника: <b>{i[1][1]}</b> и <b>{i[2][1]}</b>! 😃🎉\nСегодня мы с тобой отмечаем {n1} месяцев с дня, когда <i>{i[1][2]}</i> и {n2} месяцев с того, когда <i>{i[2][2]}</i> 🎉🎉🎉")
                await bot.send_message(cp["Bot"]["ME_ID"], f"Поздравляю, сегодня у нас с тобой аж ДВА праздника: <b>{i[1][1]}</b> и <b>{i[2][1]}</b>! 😃🎉\nСегодня мы с тобой отмечаем {n1} месяцев с дня, когда <i>{i[1][2]}</i> и {n2} месяцев с того, когда <i>{i[2][2]}</i> 🎉🎉🎉")

async def scheduler():
    sch.every().day.at("9:00").do(notify)
    sch.every().day.at("21:00").do(notify)
    sch.every().day.at("8:00").do(happy_party)
    while True:
        await sch.run_pending()
        await aio.sleep(1)
        
async def on_startup(dp): 
    aio.create_task(scheduler()) 
    aio.create_task(congratulate())

if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup)