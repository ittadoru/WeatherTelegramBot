# Импорт библиотек
from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from geopy.geocoders import Nominatim
import requests
from datetime import datetime
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from sqlite import dbStart, editProfile, createProfile, getCity, getInfo

# Локальные файлы
from weatherApp.photos import photosList
import weatherApp.keyboards as kb
from config import WEATHER_TOKEN


# Вызывается при запуске бота, подключает к БД
async def on_startup():
    await dbStart()


# Создание экземпляров
router = Router()
geolocator = Nominatim(user_agent="Weather")


# Класс FSM для связи с БД
class Req(StatesGroup):
    city = State()
    info = State()


# Команда старт, просит ввести данные в БД
@router.message(CommandStart())
async def start_msg(message: Message):
    await message.answer("Укажите свой населенный пункт, нажмите на /change")


# Основная команда, работа с БД
@router.message(Command("change"))
async def changeCity(message: Message, state: FSMContext):
    await state.set_state(Req.city)
    await message.answer("Напишите название населенного пункта")

    # Создание записи в БД для данного пользователя
    await createProfile(user_id=message.from_user.id)


# Изменение города в БД по user_id
@router.message(Req.city)
async def reqCity(message: Message, state: FSMContext):
    # Обновление информации из Req.city
    await state.update_data(city=message.text.capitalize())

    # Запрос данных из Req
    data = await state.get_data()
    await message.answer(f"Вы указали {data['city']}", reply_markup=kb.main)
    await state.set_state(Req.info)

    # Проверка существования введённого населенного пункта
    location = geolocator.geocode(data['city'])
    if location is None:
        await message.answer(f"Не могу найти такое место, повторите, нажав /change")
    else:
        await message.answer(f"Хотите ли вы получать дополнительную информацию о погоде?", reply_markup=kb.ans)




# Изменение условия доп. информации по user_id
@router.message(Req.info)
async def reqInfo(message: Message, state: FSMContext):
    # Обновление информации из Req.info
    await state.update_data(info=message.text.capitalize())
    await message.answer(f"Отлично, теперь выберите что интересует", reply_markup=kb.main)

    # Сохранение всех изменений из FSM Req в БД
    await editProfile(state, message.from_user.id)

    # Отключаем активность FSMContext
    await state.clear()


# Команда help
@router.message(Command("help"))
async def start_msg(message: Message):
    await message.answer("help")


# Функция для запроса погоды в данный момент
@router.message(F.text == "Погода сейчас")
async def weather2day(message: Message, weather_token=WEATHER_TOKEN): \

    # Подключение к БД, поиск сохранённого города
    city = await getCity(message.from_user.id)

    # Подключение к БД, поиск условия доп. информации
    get_info = await getInfo(message.from_user.id)

    # Основная работа
    try:
        # Поиск города по названию
        location = geolocator.geocode(city)

        # Получения долготы и широты для API погоды
        lat = location.latitude
        lon = location.longitude

        # Запрос в API погоды
        req = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={weather_token}&units=metric&lang=ru")

        # Парсинг ответа от запроса
        data = req.json()

        # Вспомогательные переменные после парсинга
        temp_now = data["main"]["temp"]                                                 # Температура сейчас
        feels_temp = data["main"]["feels_like"]                                         # Температура чувствуется как
        humidity = data["main"]["humidity"]                                             # Влажность
        wind_speed = data["wind"]["speed"]                                              # Скорость ветра
        sunrise = datetime.fromtimestamp(data["sys"]["sunrise"]).strftime("%H:%M")      # Рассвет
        sunset = datetime.fromtimestamp(data["sys"]["sunset"]).strftime("%H:%M")        # Закат
        desc_weather = data["weather"][0]["description"]                                # Описание погоды
        photo = data["weather"][0]["icon"]                                              # Иконка соответствующей погоды

        # Поиск id фотографии соответствующей погоды из файла photos.py
        if photo in photosList[0]:
            # Проверка условия доп. информации
            if get_info == "да":
                await message.answer_photo(photo=photosList[0][photo], caption=f"Сейчас {temp_now} С°  {desc_weather}\n\nОщущается как {feels_temp} С°\nВлажность: {humidity} %\nСкорость ветра: {wind_speed} м/с\n\nРассвет: {sunrise}\nЗакат: {sunset}")
            else:
                await message.answer_photo(photo=photosList[0][photo], caption=f"Сайчас {temp_now} С°  {desc_weather}")

    # На случай ошибки
    except Exception as ex:
        await message.reply(f"Извините, видимо не вы указали город, не понимаю что произошло не так... {ex}")


# Функция для запроса погоды на завтра
@router.message(F.text == "Погода на завтра")
async def weatherTomorrow(message: Message, weather_token=WEATHER_TOKEN):

    # Подключение к БД, поиск сохранённого города
    city = await getCity(message.from_user.id)

    # Подключение к БД, поиск условия доп. информации
    get_info = await getInfo(message.from_user.id)

    # Основная работа
    try:
        location = geolocator.geocode(city)  # Поиск города по названию

        # Получения долготы и широты для API погоды
        lat = location.latitude
        lon = location.longitude

        # Запрос в API погоды
        req = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={weather_token}&units=metric&lang=ru")

        data = req.json()  # Парсинг ответа от запроса

        # Вспомогательные переменные после парсинга
        temp_max = data["list"][0]["main"]["temp"]
        temp_min = data["list"][0]["main"]["temp"]

        # Проверка максимума и минимума
        for i in range(8):
            if temp_min > data["list"][i]["main"]["temp"]:
                temp_min = data["list"][i]["main"]["temp"]

        for i in range(8):
            if temp_max < data["list"][i]["main"]["temp"]:
                temp_max = data["list"][i]["main"]["temp"]

        # Еще вспомогательные переменные
        temp_avg = round((temp_max + temp_min) / 2)                                     # Средняя температура за день
        sunrise = datetime.fromtimestamp(data["city"]["sunrise"]).strftime("%H:%M")     # Время рассвета
        sunset = datetime.fromtimestamp(data["city"]["sunset"]).strftime("%H:%M")       # Время заката
        desc_weather = data["list"][4]["weather"][0]["description"]                     # Описание погоды
        photo = data["list"][0]["weather"][0]["icon"]                                   # Иконка соответствующей погоды

        # Поиск id фотографии соответствующей погоды из файла photos.py
        if photo in photosList[0]:
            # Проверка условия доп. информации
            if get_info == "да":
                await message.answer_photo(photo=photosList[0][photo], caption=f"В среднем {temp_avg} С°  {desc_weather}\n\nМаксимальная температура {temp_max} С°\nМинимальная температура {temp_min} С°\n\nРассвет: {sunrise}\nЗакат: {sunset}")
            else:
                await message.answer_photo(photo=photosList[0][photo], caption=f"В среднем {temp_avg} С°  {desc_weather}")

    # На случай ошибки
    except Exception as ex:
        await message.reply("Извините, видимо не вы указали город, не понимаю что произошло не так...")


# Функция для запроса погоды на 5 дней
@router.message(F.text == "Погода на 5 дней")
async def weather5day(message: Message, weather_token=WEATHER_TOKEN):

    # Подключение к БД, поиск сохранённого города
    city = await getCity(message.from_user.id)

    # Подключение к БД, поиск условия доп. информации
    get_info = await getInfo(message.from_user.id)

    # Основная работа
    try:
        location = geolocator.geocode(city)  # Поиск города по названию

        # Получения долготы и широты для API погоды
        lat = location.latitude
        lon = location.longitude

        # Запрос в API погоды
        req = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={weather_token}&units=metric&lang=ru")

        data = req.json()  # Парсинг ответа от запроса

        for i in range(0, 40, 8):

            # Вспомогательные переменные после парсинга
            temp_max = data["list"][0]["main"]["temp"]
            temp_min = data["list"][0]["main"]["temp"]

            # Проверка максимума и минимума
            for j in range(8):
                if temp_min > data["list"][i+j]["main"]["temp"]:
                    temp_min = data["list"][i+j]["main"]["temp"]

            for j in range(8):
                if temp_max < data["list"][i+j]["main"]["temp"]:
                    temp_max = data["list"][i+j]["main"]["temp"]

            temp_avg = round((temp_max + temp_min) / 2)                                 # Средняя температура за день
            desc_weather = data["list"][i+4]["weather"][0]["description"]               # Описание погоды
            date = datetime.fromtimestamp(data["list"][i]["dt"]).strftime("%d %b %Y")   # Дата дня конкретной итерации

            # Проверка условия доп. информации
            if get_info == "да":
                await message.answer(f"{date}\n\nВ среднем {temp_avg} С°  {desc_weather}\n\nМаксимальная температура {temp_max} С°\nМинимальная температура {temp_min} С°")
            else:
                await message.answer(f"{date}\n\nВ среднем {temp_avg} С°  {desc_weather}")

    # На случай ошибки
    except Exception as ex:
        await message.reply(f"Извините, видимо не вы указали город, не понимаю что произошло не так... {ex}")


# Любой другой несанкционированный запрос
@router.message()
async def defaultAnswer(message: Message):
    await message.answer_photo(photo=message.text)
