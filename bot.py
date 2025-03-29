import os
import requests
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()

# API ключ для RapidAPI
API_KEY = "ae6c77f019msh6cad65d207e4245p1e3c08jsn66ce1bd839c3"
VIN_API_URL = "https://vin-decoder-api-usa.p.rapidapi.com/vin"

# Телеграм токен
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Главный экран с кнопками
def get_main_menu():
    keyboard = [
        ["🔍 Check Car by VIN"],
        ["❓ FAQ"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Получение данных по VIN
def get_car_info(vin_code):
    headers = {
        'X-RapidAPI-Key': API_KEY,
        'X-RapidAPI-Host': 'vin-decoder-api-usa.p.rapidapi.com'
    }
    params = {
        'v': vin_code
    }
    response = requests.get(VIN_API_URL, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Стартовая команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to USA VIN Check Bot! Choose an option below:", 
        reply_markup=get_main_menu()
    )

# Обработка ввода VIN
async def handle_vin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    vin_code = update.message.text.strip()
    
    # Проверка формата VIN (17 символов)
    if len(vin_code) != 17:
        await update.message.reply_text("Пожалуйста, введите действительный VIN код из 17 символов.")
        return
    
    # Получаем данные о машине
    car_data = get_car_info(vin_code)
    
    if car_data:
        # Формируем сообщение с информацией о машине
        car_info = f"**Информация о машине для VIN: {vin_code}**\n\n"
        car_info += f"**Марка**: {car_data.get('make', 'N/A')}\n"
        car_info += f"**Модель**: {car_data.get('model', 'N/A')}\n"
        car_info += f"**Год выпуска**: {car_data.get('year', 'N/A')}\n"
        car_info += f"**Тип двигателя**: {car_data.get('engine', 'N/A')}\n"
        car_info += f"**Тип топлива**: {car_data.get('fuel', 'N/A')}\n"
        car_info += f"**Трансмиссия**: {car_data.get('transmission', 'N/A')}\n"
        
        await update.message.reply_text(car_info)
    else:
        await update.message.reply_text("Извините, информация по этому VIN не найдена.")

# Обработка кнопки FAQ
async def handle_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    faq = """**FAQ:**
    - Что такое VIN? 
      VIN (Vehicle Identification Number) — это уникальный код, который используется для идентификации транспортных средств.
    
    - Как использовать VIN Check?
      Вы можете ввести VIN номер, чтобы узнать спецификации автомобиля, историю аварий и многое другое."""
    
    await update.message.reply_text(faq)

# Основная обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🔍 Check Car by VIN":
        await update.message.reply_text("Пожалуйста, введите VIN код автомобиля:")
    elif text == "❓ FAQ":
        await handle_faq(update, context)
    else:
        await update.message.reply_text("Извините, я не понял ваш запрос. Пожалуйста, выберите опцию из меню.", reply_markup=get_main_menu())

# Настройка бота
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("USA VIN Check Bot is running...")
app.run_polling()