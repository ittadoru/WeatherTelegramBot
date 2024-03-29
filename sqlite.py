import sqlite3 as sq


# Функция коннекта к базе данных, или её создания на случай, если её нет
async def dbStart():
    global db, cur

    # Коннект к БД
    db = sq.connect('users.db')
    cur = db.cursor()

    # Создание БД
    cur.execute("CREATE TABLE IF NOT EXISTS profile(user_id TEXT PRIMARY KEY, city TEXT, info TEXT)")

    db.commit()


# Функция создания записи соответствующего пользователя с его городом и условием доп. информации
async def createProfile(user_id):
    # Выбор 1 записи по значению user_id
    user = cur.execute("SELECT 1 FROM profile WHERE user_id == '{key}'".format(key=user_id)).fetchone()

    # Если user отсутствует, мы создадим его запись
    if not user:
        cur.execute("INSERT INTO profile VALUES(?, ?, ?)", (user_id, '', ''))
        db.commit()


# Функция редактирования параметров пользователя
async def editProfile(state, user_id):
    data = await state.get_data()   # Получение данных из FSM

    # Сохранение этих данных в БД
    cur.execute("UPDATE profile SET city = '{}', info = '{}' WHERE user_id = '{}'".format(data["city"], data["info"], user_id))

    db.commit()


# Функция, для получения города конкретного пользователя
async def getCity(user_id):
    # Выбор города по конкретному user_id
    cur.execute("SELECT city FROM profile WHERE user_id = '{}'".format(user_id))

    # Сохраняем в строку
    city_tuple = cur.fetchone()

    # Проверяем, есть ли результат запроса, и извлекаем значение города
    if city_tuple:
        city = city_tuple[0]
    else:
        city = None
    return city


# Функция, для получения условия доп. информации конкретного пользователя
async def getInfo(user_id):
    # Выбор условия по конкретному user_id
    cur.execute("SELECT info FROM profile WHERE user_id = '{}'".format(user_id))

    # Сохраняем в строку
    info_tuple = cur.fetchone()

    # Проверяем, есть ли результат запроса, и извлекаем значение условия
    if info_tuple:
        if info_tuple[0] == "Да, хочу":
            return "да"
        else:
            return "нет"
