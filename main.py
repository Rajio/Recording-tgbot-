import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from database import init_db, add_appointment, check_appointment_exists, get_free_slots
from datetime import datetime, timedelta

API_TOKEN = '7396155889:AAEgkN_fb0gtAPgTBBMOmW3b3sfdW6kt0fg'

logging.basicConfig(level=logging.INFO)

# Ініціалізація бази даних
init_db()

user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Привіт! Використовуйте команду /register, щоб записатися на прийом до психолога.")

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Введіть ваше ім'я:")
    user_data[update.message.from_user.id] = {'step': 'name'}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    step = user_data.get(user_id, {}).get('step')

    if step == 'name':
        user_data[user_id]['name'] = update.message.text
        await update.message.reply_text("Введіть ваш номер телефону:")
        user_data[user_id]['step'] = 'phone'
    
    elif step == 'phone':
        phone_number = update.message.text
        user_data[user_id]['phone'] = phone_number
        await choose_date(update, context)

async def choose_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = []
    today = datetime.now()
    
    for i in range(5):  # Пропонуємо дати на 5 днів вперед
        day = today + timedelta(days=i)
        keyboard.append([InlineKeyboardButton(day.strftime('%Y-%m-%d'), callback_data=day.strftime('%Y-%m-%d'))])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Виберіть бажану дату:", reply_markup=reply_markup)
    user_data[update.message.from_user.id]['step'] = 'date'

async def handle_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    selected_date = query.data
    await query.answer()  # Відповісти на запит
    await query.message.reply_text(f"Ви вибрали дату: {selected_date}. Тепер виберіть вільний час.")
    
    # Отримуємо вільні слоти
    free_slots = get_free_slots(selected_date)
    if free_slots:
        keyboard = [[InlineKeyboardButton(slot.strftime('%H:%M'), callback_data=f"{selected_date} {slot.strftime('%H:%M')}")] for slot in free_slots]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Виберіть вільний час:", reply_markup=reply_markup)
        user_data[user_id]['step'] = 'time'
        user_data[user_id]['selected_date'] = selected_date
    else:
        await query.message.reply_text("На жаль, вільних слотів немає на цей день.")

async def handle_time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    selected_time = query.data.split(' ')[1]  # Витягти тільки час
    selected_date = user_data[user_id]['selected_date']
    
    logging.info(f"Selected date: {selected_date}, Selected time: {selected_time}")
    logging.info(f"Raw data received for appointment: {selected_date} {selected_time}")

    try:
        appointment_time = datetime.strptime(f"{selected_date} {selected_time}", '%Y-%m-%d %H:%M')

        if check_appointment_exists(appointment_time.strftime('%Y-%m-%d %H:%M')):
            await query.answer("Цей час вже зайнятий, виберіть інший.")
            return
        
        end_time = appointment_time + timedelta(hours=2)
        add_appointment(user_id, user_data[user_id]['name'], user_data[user_id]['phone'], appointment_time.strftime('%Y-%m-%d %H:%M'))

        await query.answer()
        await query.message.reply_text(f"Ваш прийом заплановано на {appointment_time.strftime('%Y-%m-%d %H:%M')} до {end_time.strftime('%H:%M')}.")
        del user_data[user_id]
    except ValueError as e:
        logging.error(f"ValueError while processing appointment: {e}")
        await query.answer("Сталася помилка при обробці даних.")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        await query.answer("Сталася неочікувана помилка. Спробуйте ще раз.")

def main() -> None:
    app = ApplicationBuilder().token(API_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register", register))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.add_handler(CallbackQueryHandler(handle_date_selection, pattern=r'^\d{4}-\d{2}-\d{2}$'))
    app.add_handler(CallbackQueryHandler(handle_time_selection, pattern=r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$'))

    app.run_polling()

if __name__ == '__main__':
    main()
