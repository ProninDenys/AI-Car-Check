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
c.execute('''CREATE TABLE IF NOT EXISTS service_requests (
    user_id INTEGER,
    brand TEXT,
    model TEXT,
    year TEXT,
    mileage INTEGER,
    unit TEXT,
    fuel TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
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

# === SERVICE REPORT ===
def get_maintenance_report(brand, model, year, mileage, unit, fuel):
    if unit.lower() == "miles":
        mileage = round(mileage * 1.6)

    past, upcoming = [], []

    def check(km, task):
        if mileage >= km:
            past.append(f"{km} km — {task}")
        else:
            upcoming.append(f"{km} km — {task}")

    check(15000, "Oil & Filter Change")
    check(30000, "Air Filter Replacement")
    check(60000, "Spark Plugs Replacement")
    check(90000, "Timing Belt Inspection")
    check(120000, "Spark Plugs Replacement Again")
    check(150000, "Suspension & Steering Check")
    check(180000, "Timing Belt Re-check")

    report = f"\n🔧 Service Report for {brand} {model} ({year}), {mileage} km, {fuel}\n\n"
    report += "📌 What should have been done:\n" + ("\n".join(f"\u2705 {item}" for item in past) if past else "None") + "\n\n"
    report += "🔹 Upcoming recommendations:\n" + ("\n".join(f"📑 {item}" for item in upcoming) if upcoming else "None")
    return report

# === FAQ ===
faq_data = {
    "Learner Permit": "To get a Learner Permit in Ireland...",
    "New Driver": "As a new driver in Ireland...",
    "How to buy a car": "When buying a car in Ireland...",
    "Registration": "To register your vehicle...",
    "Road Tax": "Road tax can be paid on motortax.ie...",
    "NCT": "NCT is a mandatory vehicle test...",
    "Required Documents": "You typically need logbook, ID, insurance..."
}

# === START ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = {"step": None}

    keyboard = [
        ["\U0001F697 Check Car by Reg Number"],
        ["\U0001F4C4 Estimate Insurance"],
        ["\U0001F4D1 History"],
        ["\U0001F527 Service & Maintenance"],
        ["\U0001F4A1 FAQ"],
        ["\U0001F504 Start Over"]
    ]
    await update.message.reply_text("Welcome to AutoCheck AI!", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

# === CALLBACK ===
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data in faq_data:
        await query.message.reply_text(faq_data[query.data])
    elif query.data == "back_to_menu":
        await start(update, context)
    elif query.data == "download_pdf":
        user_id = query.from_user.id
        path = f"insurance_estimate_{user_id}.pdf"
        if os.path.exists(path):
            await query.message.reply_chat_action(ChatAction.UPLOAD_DOCUMENT)
            await query.message.reply_document(document=open(path, "rb"))
            os.remove(path)
        else:
            await query.message.reply_text("PDF not found. Please calculate insurance first.")

# === MESSAGE ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # (Обработчик оставлен без изменений, сюда вставляется логика страховки, сервисов, FAQ, истории и шагов)
    pass

# === APP INIT ===
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_callback))

print("AI Car Check Bot is running...")
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
app.run_polling()
