import asyncio
import logging
import datetime
import scrapetube
import random
from pytube import YouTube
import os
from moviepy.editor import *
from CONFIG import settings
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.types import FSInputFile
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import json
import requests

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=settings['token_tg'])
# Диспетчер
dp = Dispatcher()
scheduler = AsyncIOScheduler()
     
# Открываем json файл с каналами
with open("data.json", "r") as f:
    data = json.load(f)


# Функция на отправку видео каждый день

async def send_video_every():
    a = False
    b = 0
    for vid in data:
        videos = scrapetube.get_channel(vid)
        for video in videos:
            print(video['videoId'])
            if video['videoId'] not in vid_list_al:
                yt = YouTube(f'https://www.youtube.com/watch?v={video["videoId"]}')
                print(f'https://www.youtube.com/watch?v={video["videoId"]}')
                stream = yt.streams.filter(only_audio=True).first()
                stream.download(filename=f"{yt.title}.mp3")
                audio = FSInputFile(f"{yt.title}.mp3")
                await bot.send_audio(chat_id=settings['user_wl'], audio=audio, caption=f"Держи свой подкаст под названием {yt.title}!\n{yt.watch_url}")
                os.remove(f"{yt.title}.mp3") 
                a = True 
                vid_list_al[b] = video['videoId']
            break
        b+=1 
    if a == False:
        await bot.send_message(chat_id=settings['user_wl'], caption=f"Новых роликов не вышло")


# Кнопка настройки
@dp.message(F.text.lower() == "настройки")
async def setting(message: types.Message) -> None:
    if message.from_user.id == settings['user_wl']:
        await message.answer("Если вы хотите добавить или удалить канал из списка каналов, просто напишите его название в чат")
    else:
        await message.answer(f"Привет, тебя нету в вайт листе, так что ты не можешь пользоваться ботом\nТвой id для добавления в white list: {message.from_user.id}")



# Кнопка информации
@dp.message(F.text.lower() == "информация")
async def information(message: types.Message):
    if message.from_user.id == settings['user_wl']:
        a = ""
        for i in data:
            a = a + f"\nhttps://www.youtube.com/channel/{i}"
        await message.answer(f"Список каналов:{a}")
    else:
        await message.answer(f"Привет, тебя нету в вайт листе, так что ты не можешь пользоваться ботом\nТвой id для добавления в white list: {message.from_user.id}")


# Кнопка загрузки подкаста
@dp.message(F.text.lower() == "загрузить подкаст")
async def dowload_without(message: types.Message):
    if message.from_user.id == settings['user_wl']:
        videos = scrapetube.get_channel(random.choice(data))
        i = 0 
        vid_list = []
        for video in videos:
            print(video['videoId'])
            vid_list.append(video['videoId'])
            i = i+1
            if i == 10:
                break
        yt = YouTube(f'https://www.youtube.com/watch?v={random.choice(vid_list)}')
        stream = yt.streams.filter(only_audio=True).first()
        stream.download(filename=f"{yt.title}.mp3")
        audio = FSInputFile(f"{yt.title}.mp3")
        await message.answer_audio(audio=audio, caption=f"Держи свой подкаст под названием {yt.title}!\n{yt.watch_url}")
        os.remove(f"{yt.title}.mp3")
    else:
        await message.answer(f"Привет, тебя нету в вайт листе, так что ты не можешь пользоваться ботом\nТвой id для добавления в white list: {message.from_user.id}")


# /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id == settings['user_wl']:
        kb = [
            [
                types.KeyboardButton(text="Настройки"),
                types.KeyboardButton(text="Информация"),
                types.KeyboardButton(text="Загрузить подкаст"),
            ],
        ]
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True,
            input_field_placeholder="Меню"
        )
        await message.answer("Приветствую, данный бот будет присылать тебе подкаст каждый день из твоего списка каналов(информация и настройки)", reply_markup=keyboard)
    else:
        await message.answer(f"Привет, тебя нету в вайт листе, так что ты не можешь пользоваться ботом\nТвой id для добавления в white list: {message.from_user.id}")


# Запуск, сохранение последних видео, загрузка задания на отправку видео каждый день, запуск бота
async def main():
    for vid in data:
        videos = scrapetube.get_channel(vid)
        for video in videos:
            print(video['videoId'])
            vid_list_al.append(video['videoId'])
            break
    today = datetime.datetime.today().strftime("%Y-%m-%d")
    time = int(datetime.datetime.today().strftime("%H"))
    print("01:00:00" + f" {today}")
    if time >= 1:
        today = datetime.datetime.today() + datetime.timedelta(days=1)
        today = today.strftime("%Y-%m-%d")
        print(today)
    scheduler.add_job(send_video_every, "interval", seconds=86400, start_date=f"{today} " + "01:00:00")
    scheduler.start()
    await dp.start_polling(bot)


# Функция при получении сообщения
@dp.message()
async def name(message: types.Message):
    if message.from_user.id == settings['user_wl']:
        a = True
        b = 0
        channel_id = requests.get(f'https://www.googleapis.com/youtube/v3/search?part=id&q={message.text}&type=channel&key={settings["token_google"]}').json()['items'][0]['id']['channelId']
        if len(channel_id)==24:
            for i in data:
                if channel_id == i:
                    data.pop(b)
                    a = False
                b = b + 1
            if a == True:
                data.append(channel_id)
                with open('data.json', 'w') as outfile:
                    json.dump(data, outfile, indent=4)
                await message.answer(f"Добавил в список каналов на отправку подкастов:\nhttps://www.youtube.com/channel/{channel_id}\n\nЕсли вы хотите удалить его из списка, напишите название ещё раз")
            else:
                await message.answer(f"Данный канал удалён из списка каналов:\nhttps://www.youtube.com/channel/{channel_id}")
    else:
        await message.answer(f"Привет, тебя нету в вайт листе, так что ты не можешь пользоваться ботом\nТвой id для добавления в white list: {message.from_user.id}")



if __name__ == "__main__":
    vid_list_al = []
    asyncio.run(main())