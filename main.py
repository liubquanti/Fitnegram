from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
import firebase_admin
from firebase_admin import credentials, firestore
from config import TOKEN, FIREBASE
from handlers.exercise import handle_add_exercise
from handlers.workout import handle_workout, handle_workout_button
from handlers import MAIN_MENU, ADD_DAY, ADD_EXERCISE, WORKOUT_PROGRESS, CONFIRM_DELETE, get_main_menu_keyboard, get_day_menu_keyboard

cred = credentials.Certificate(FIREBASE)
firebase_admin.initialize_app(cred)
db = firestore.client()

async def start(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    user_ref = db.collection('users').document(str(user_id))
    
    if not user_ref.get().exists:
        user_ref.set({
            'name': update.effective_user.first_name,
            'created_at': firestore.SERVER_TIMESTAMP
        })
    
    await update.message.reply_text(
        "Вітаю! Оберіть день тренування або створіть новий:",
        reply_markup=get_main_menu_keyboard(user_id)
    )
    return MAIN_MENU

async def handle_main_menu(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == "➕ Додати день":
        await update.message.reply_text("Введіть назву нового дня тренувань:")
        return ADD_DAY
    elif text == "🏋️‍♂️ Почати тренування":
        return await handle_workout(update, context)
    elif text == "❌ Видалити день":
        current_day = context.user_data.get('current_day')
        if current_day:
            await update.message.reply_text(
                f"Ви впевнені, що хочете видалити день '{current_day}'?",
                reply_markup=get_confirm_keyboard()
            )
            return CONFIRM_DELETE
        return MAIN_MENU
    elif text == "↩️ Назад":
        await update.message.reply_text(
            "Головне меню:",
            reply_markup=get_main_menu_keyboard(user_id)
        )
        return MAIN_MENU
    else:
        day_ref = db.collection(str(user_id)).document(text)
        doc = day_ref.get()
        if doc.exists:
            context.user_data['current_day'] = text
            exercises = doc.to_dict().get('exercises', [])
            keyboard = get_day_menu_keyboard()
            await update.message.reply_text(
                f"День: {text}\nВправи:\n" + "\n".join([f"- {ex['name']} ({ex['weight']}kg)" for ex in exercises]),
                reply_markup=keyboard
            )
    return MAIN_MENU

async def handle_confirm_delete(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    user_id = update.effective_user.id
    current_day = context.user_data.get('current_day')
    
    if text == "✅ Так, видалити":
        db.collection(str(user_id)).document(current_day).delete()
        await update.message.reply_text(
            "День видалено!",
            reply_markup=get_main_menu_keyboard(user_id)
        )
    else:
        await update.message.reply_text(
            "Видалення скасовано",
            reply_markup=get_main_menu_keyboard(user_id)
        )
    return MAIN_MENU

async def handle_add_day(update: Update, context: CallbackContext) -> int:
    day_name = update.message.text
    user_id = update.effective_user.id
    
    day_ref = db.collection(str(user_id)).document(day_name)
    day_ref.set({
        'name': day_name,
        'exercises': [],
        'created_at': firestore.SERVER_TIMESTAMP
    })
    
    await update.message.reply_text("Додайте першу вправу у форматі: Назва, вага")
    context.user_data['current_day'] = day_name
    return ADD_EXERCISE

async def handle_done(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    await update.message.reply_text(
        "Додавання вправ завершено!",
        reply_markup=get_main_menu_keyboard(user_id)
    )
    return MAIN_MENU

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

def main():
    application = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)
            ],
            ADD_DAY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_day)
            ],
            ADD_EXERCISE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_exercise),
                CommandHandler('done', handle_done)
            ],
            WORKOUT_PROGRESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_workout_button)
            ],
            CONFIRM_DELETE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_confirm_delete)
            ]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()