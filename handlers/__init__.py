from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import CallbackContext
from firebase_admin import firestore

MAIN_MENU, ADD_DAY, ADD_EXERCISE, WORKOUT_PROGRESS, CONFIRM_DELETE = range(5)

def get_main_menu_keyboard(user_id):
    db = firestore.client()
    days_ref = db.collection(str(user_id)).stream()
    days = [day.id for day in days_ref]
    keyboard = [[KeyboardButton(day)] for day in days]
    keyboard.append([KeyboardButton("➕ Додати день")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_workout_keyboard():
    keyboard = [
        [KeyboardButton("✅ Виконано")],
        [KeyboardButton("⏭️ Наступна вправа")],
        [KeyboardButton("🏁 Завершити тренування")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_day_menu_keyboard():
    keyboard = [
        [KeyboardButton("🏋️‍♂️ Почати тренування")],
        [KeyboardButton("❌ Видалити день")],
        [KeyboardButton("↩️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_confirm_keyboard():
    keyboard = [
        [KeyboardButton("✅ Так, видалити")],
        [KeyboardButton("❌ Ні, скасувати")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)