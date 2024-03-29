from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Клавиатура с выбором погоды
main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Погода сейчас")],
    [KeyboardButton(text="Погода на завтра")],
    [KeyboardButton(text="Погода на 5 дней")]
], resize_keyboard=True, input_field_placeholder="Что вы хотите узнать?")

# Клавиатура с выбором условия доп. информации
ans = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Да, хочу")],
    [KeyboardButton(text="Нет, не хочу")],
], resize_keyboard=True, input_field_placeholder="Хотите получать?")
