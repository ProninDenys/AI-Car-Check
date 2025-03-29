import os
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Загружаем .env файл
load_dotenv()

# Ключ API RapidAPI и токен бота
API_KEY = os.getenv("RAPIDAPI_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
VIN_API_URL = "https://vin-decoder-api-usa.p.rapidapi.com/vin"

# Главное меню для бота
def get_main_menu():
    keyboard = [
        ["🔍 Check Car by VIN"],
        ["❓ FAQ"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Функция для получения информации по VIN
def get_car_info(vin_code):
    headers = {
        'X-RapidAPI-Key': API_KEY,
        'X-RapidAPI-Host': 'vin-decoder-api-usa.p.rapidapi.com'
    }
    params = {
        'v': vin_code
    }
    try:
        response = requests.get(VIN_API_URL, headers=headers, params=params)
        response.raise_for_status()  # Проверка на успешный ответ
        return response.json()  # Возвращаем данные в формате JSON
    except requests.exceptions.RequestException as e:
        print(f"Error fetching VIN data: {e}")
        return None

# Стартовая команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to USA VIN Check Bot! Choose an option below:", 
        reply_markup=get_main_menu()
    )

# Обработка VIN
async def handle_vin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    vin_code = update.message.text.strip()
    
    # Получаем данные по VIN
    car_data = get_car_info(vin_code)
    
    if car_data:
        car_info = f"**Car Info for VIN: {vin_code}**\n\n"
        car_info += f"**Make**: {car_data.get('make', 'N/A')}\n"
        car_info += f"**Model**: {car_data.get('model', 'N/A')}\n"
        car_info += f"**Year**: {car_data.get('year', 'N/A')}\n"
        car_info += f"**Engine Type**: {car_data.get('engine', 'N/A')}\n"
        car_info += f"**Fuel Type**: {car_data.get('fuel', 'N/A')}\n"
        car_info += f"**Transmission**: {car_data.get('transmission', 'N/A')}\n"
        
        await update.message.reply_text(car_info)
    else:
        await update.message.reply_text("Sorry, no information found for this VIN. Please check the VIN and try again.")

# Обработка FAQ
async def handle_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    faq = """**FAQ:**
    - What is a VIN? 
      A Vehicle Identification Number (VIN) is a unique code used by the automotive industry to identify individual motor vehicles.
    
    - How can I use VIN Check?
      You can enter a VIN to check the vehicle's specifications, accident history, and more."""
    
    await update.message.reply_text(faq)

# Основная обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🔍 Check Car by VIN":
        await update.message.reply_text("Please enter the VIN number of the car:")
    elif text == "❓ FAQ":
        await handle_faq(update, context)
    else:
        await update.message.reply_text("Sorry, I didn't understand that. Please choose an option from the menu.", reply_markup=get_main_menu())

# Настройка бота
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("USA VIN Check Bot is running...")
app.run_polling()