from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import CallbackContext
from firebase_admin import firestore
from . import MAIN_MENU, WORKOUT_PROGRESS, get_main_menu_keyboard, get_workout_keyboard

async def handle_workout(update: Update, context: CallbackContext) -> int:
    db = firestore.client()
    user_id = update.effective_user.id
    current_day = context.user_data.get('current_day')
    
    if not current_day:
        await update.message.reply_text("Спочатку оберіть день тренування")
        return MAIN_MENU
        
    day_ref = db.collection(str(user_id)).document(current_day)
    day_data = day_ref.get().to_dict()
    
    if not day_data:
        await update.message.reply_text("День тренування не знайдено")
        return MAIN_MENU
        
    exercises = day_data.get('exercises', [])
    incomplete_exercises = [ex for ex in exercises if not ex.get('completed', False)]
    
    if 'current_exercise_index' not in context.user_data:
        context.user_data['current_exercise_index'] = 0
    
    if not incomplete_exercises:
        await update.message.reply_text(
            "🎉 Всі вправи виконано! Тренування завершено! 💪",
            reply_markup=get_main_menu_keyboard(user_id)
        )
        for ex in exercises:
            ex['completed'] = False
        day_ref.update({'exercises': exercises})
        context.user_data.pop('current_exercise_index', None)
        return MAIN_MENU
    
    current_index = context.user_data['current_exercise_index'] % len(incomplete_exercises)
    current_exercise = incomplete_exercises[current_index]
    
    await update.message.reply_text(
        f"Поточна вправа:\n{current_exercise['name']} - {current_exercise['weight']}kg",
        reply_markup=get_workout_keyboard()
    )
    return WORKOUT_PROGRESS

async def handle_workout_button(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    user_id = update.effective_user.id
    current_day = context.user_data.get('current_day')
    db = firestore.client()
    
    if text == "✅ Виконано":
        day_ref = db.collection(str(user_id)).document(current_day)
        day_data = day_ref.get().to_dict()
        exercises = day_data.get('exercises', [])
        
        incomplete_exercises = [ex for ex in exercises if not ex.get('completed', False)]
        if incomplete_exercises:
            current_index = context.user_data.get('current_exercise_index', 0) % len(incomplete_exercises)
            current_exercise_name = incomplete_exercises[current_index]['name']
            
            for ex in exercises:
                if ex['name'] == current_exercise_name and not ex.get('completed', False):
                    ex['completed'] = True
                    break
            
            day_ref.update({'exercises': exercises})
            
            context.user_data['current_exercise_index'] = 0
            
        return await handle_workout(update, context)
        
    elif text == "⏭️ Наступна вправа":
        context.user_data['current_exercise_index'] = context.user_data.get('current_exercise_index', 0) + 1
        return await handle_workout(update, context)
        
    elif text == "🏁 Завершити тренування":
        context.user_data.pop('current_exercise_index', None)
        await update.message.reply_text(
            "Тренування завершено! 💪",
            reply_markup=get_main_menu_keyboard(user_id)
        )
        return MAIN_MENU