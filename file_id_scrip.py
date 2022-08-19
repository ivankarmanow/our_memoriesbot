from aiogram import Bot, Dispatcher, executor, types, exceptions
from aiogram.types import InputFile
import os
import psycopg2
import asyncio as ao

bot = Bot(token="5469093216:AAEWwh9wABs4SA1FsemXTPJYeaVWWKV-oVs", parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

conn = psycopg2.connect(user="ivan", password="!QWE#2asd", host="localhost", port="5432", database="mydb")

@dp.errors_handler(exception=exceptions.RetryAfter)
async def exception_handler(update: types.Update, exception: exceptions.RetryAfter):
    print("Sleep for 5 seconds")
    await ao.sleep(5)
    return True

@dp.message_handler(text="/start")
async def main(msg: types.Message):
    photos = os.listdir("photo")
    for i in photos:
       img = InputFile("photo/"+i)
       message = await bot.send_photo(1365693965, img, disable_notification=True)
       cur = conn.cursor()
       file_id = message.photo[-1].file_id
       cur.execute(f"INSERT INTO files_id (file_id, filename) VALUES ('{file_id}', '{i}');")
       cur.close()
       conn.commit()
       await ao.sleep(0.5)
    musics = os.listdir("music")
    for j in musics:
        cur = conn.cursor()
        tr = InputFile("music/"+j)
        message = await bot.send_audio(1365693965, tr, disable_notification=True)
        file_id = message.audio[-1].file_id
        cur.execute("INSERT INTO files_id (file_id, filename) VALUES ({file_id}, {i});")
        cur.close()
        file_id = message.audio.file_id
        print(file_id, j)
        cur.execute(f"INSERT INTO files_id (file_id, filename) VALUES ('{file_id}', '{j}');")
        cur.close()
        conn.commit()
        await ao.sleep(0.5)

if __name__ == "__main__":
    executor.start_polling(dp)
