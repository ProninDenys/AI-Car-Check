import os
import random
import sqlite3
import sys
import asyncio
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ChatAction
from reportlab.pdfgen import canvas
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
user_states = {}

# === INIT DATABASE ===
conn = sqlite3.connect("insurance.db")
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS insurance_requests (
    user_id INTEGER,
    age INTEGER,
    license_year INTEGER,
    car_year INTEGER,
    engine INTEGER,
    fuel TEXT,
    owners INTEGER,
    estimate INTEGER
)''')
conn.commit()
conn.close()

# === PDF GENERATION ===
def generate_pdf(user_id, data, estimate):
    filename = f"insurance_estimate_{user_id}.pdf"
    c = canvas.Canvas(filename)
    c.setFont("Helvetica", 12)
    c.drawString(100, 800, "Insurance Estimate Report (Ireland)")
    c.drawString(100, 770, f"Driver Age: {data['age']}")
    c.drawString(100, 750, f"Driving Experience: {2024 - data['license_year']} years")
    c.drawString(100, 730, f"Car Year: {data['car_year']}")
    c.drawString(100, 710, f"Engine: {data['engine']}cc")
    c.drawString(100, 690, f"Fuel: {data['fuel']}")
    c.drawString(100, 670, f"Owners: {data['owners']}")
    c.drawString(100, 640, f"Estimated Insurance: EUR {estimate}/year")
    c.save()
    return filename

# === START ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_states:
        user_states[user_id] = {"step": None}

    keyboard = [["\U0001F697 Check Car by Reg Number"], ["\U0001F4C4 Estimate Insurance"], ["\U0001F504 Start Over"], ["\U0001F4D1 History"], ["\U0001F527 Service & Maintenance"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text("Welcome to AutoCheck AI!\n\nChoose a feature below to begin:", reply_markup=reply_markup)

# === CALLBACK HANDLER ===
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "download_pdf":
        user_id = query.from_user.id
        pdf_path = f"insurance_estimate_{user_id}.pdf"
        if os.path.exists(pdf_path):
            await query.message.reply_chat_action(ChatAction.UPLOAD_DOCUMENT)
            await query.message.reply_document(document=open(pdf_path, "rb"))
            os.remove(pdf_path)
        else:
            await query.message.reply_text("PDF not found. Please calculate insurance first.")

# === SERVICE LOGIC ===
def get_maintenance_report(brand, model, year, mileage, unit, fuel):
    if unit.lower() == "miles":
        mileage = round(mileage * 1.6)

    past = []
    upcoming = []

    if mileage >= 15000:
        past.append("Oil & Filter Change (every 10–15k km)")
    if mileage >= 30000:
        past.append("Air Filter Change")
    if mileage >= 60000:
        past.append("Spark Plugs Replacement")
    if mileage >= 90000:
        past.append("Timing Belt Inspection")
    if mileage >= 120000:
        past.append("Spark Plugs Replacement again")

    if mileage < 150000:
        upcoming.append("150,000 km: Suspension & Steering Inspection")
    if mileage < 180000:
        upcoming.append("180,000 km: Timing Belt Check")
        upcoming.append("180,000 km: Spark Plugs")

    report = f"\n🔧 Service Report for {brand} {model} ({year}), {mileage} km, {fuel}\n\n"
    report += "📌 What should have been done:\n" + ("\n".join(f"✔ {item}" for item in past) if past else "None") + "\n\n"
    report += "📍 Upcoming recommendations:\n" + ("\n".join(f"⚠️ {item}" for item in upcoming) if upcoming else "None")

    return report

# === MESSAGE HANDLER ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_states:
        user_states[user_id] = {"step": None}

    user_data = user_states[user_id]
    step = user_data.get("step")

    if text == "\U0001F527 Service & Maintenance":
        user_data["step"] = "brand"
        await update.message.reply_text("Enter your car brand (e.g. Toyota):")
        return

    if step == "brand":
        user_data["brand"] = text
        user_data["step"] = "model"
        await update.message.reply_text("Enter your car model (e.g. Corolla):")
    elif step == "model":
        user_data["model"] = text
        user_data["step"] = "year"
        await update.message.reply_text("Enter year of manufacture (e.g. 2016):")
    elif step == "year":
        user_data["year"] = text
        user_data["step"] = "mileage"
        await update.message.reply_text("Enter current mileage (number only):")
    elif step == "mileage":
        user_data["mileage"] = int(text)
        user_data["step"] = "unit"
        await update.message.reply_text("Mileage unit: km or miles?")
    elif step == "unit":
        user_data["unit"] = text
        user_data["step"] = "fuel"
        await update.message.reply_text("Fuel type: Petrol / Diesel / Electric / Hybrid")
    elif step == "fuel":
        user_data["fuel"] = text

        report = get_maintenance_report(
            user_data['brand'], user_data['model'], user_data['year'],
            user_data['mileage'], user_data['unit'], user_data['fuel']
        )
        await update.message.reply_text(report)
        user_states[user_id]["step"] = None
    else:
        await update.message.reply_text("Please select an option from the menu using /start.")

# === APP INIT ===
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_callback))

print("AI Car Check Bot is running...")
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
app.run_polling()
