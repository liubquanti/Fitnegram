from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext
from firebase_admin import firestore
from . import MAIN_MENU, ADD_EXERCISE

async def handle_add_exercise(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    if ',' not in text:
        await update.message.reply_text("Введіть вправу у форматі: Назва, вага")
        return ADD_EXERCISE
        
    try:
        name, weight = text.split(',')
        user_id = update.effective_user.id
        current_day = context.user_data['current_day']
        
        db = firestore.client()
        day_ref = db.collection(str(user_id)).document(current_day)
        day_ref.update({
            'exercises': firestore.ArrayUnion([{
                'name': name.strip(),
                'weight': float(weight.strip()),
                'completed': False
            }])
        })
        
        await update.message.reply_text(
            "Вправу додано! Додайте ще одну або натисніть /done щоб завершити"
        )
        return ADD_EXERCISE
        
    except ValueError:
        await update.message.reply_text("Неправильний формат. Спробуйте ще раз (Назва, вага)")
        return ADD_EXERCISE