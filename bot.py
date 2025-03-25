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

    keyboard = [["\U0001F697 Check Car by Reg Number"], ["\U0001F4C4 Estimate Insurance"],
                ["\U0001F4A1 FAQ"], ["\U0001F504 Start Over"], ["\U0001F4D1 History"]]
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

# === FAQ TEXT ===
faq_data = {
    "Learner Permit": "To get a Learner Permit in Ireland, you must complete the theory test, apply online at NDLS.ie, and provide proof of address, ID, and residency.",
    "New Driver": "As a new driver, you must display 'L' plates, drive with a fully licensed driver if required, and follow beginner restrictions until fully licensed.",
    "How to buy a car": "You can buy a car from a dealer or privately. Check the NCT, tax, ownership history, and always sign a contract with proof of payment.",
    "Registration": "After buying a car, register it at motor tax office or online (for new imports). You'll need proof of ownership and identification.",
    "Road Tax": "You can pay Road Tax online at motortax.ie using the vehicle registration number and PIN. The amount depends on engine size or CO2 emissions.",
    "NCT": "NCT is Ireland's National Car Test. It's required every 1–2 years depending on the vehicle age. Book on ncts.ie.",
    "Required Documents": "Typical documents for buying a car include Vehicle Registration Certificate (logbook), proof of ID, insurance, and roadworthiness certificates."
}

# === MESSAGE HANDLER ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_states:
        user_states[user_id] = {"step": None}

    user_data = user_states[user_id]
    step = user_data.get("step")

    if text == "\U0001F504 Start Over":
        user_states[user_id] = {"step": None}
        await update.message.reply_text("Restarted. Use /start to begin again.")
        return

    if text == "\U0001F4D1 History":
        conn = sqlite3.connect("insurance.db")
        c = conn.cursor()
        c.execute("SELECT age, license_year, car_year, engine, fuel, owners, estimate FROM insurance_requests WHERE user_id=? ORDER BY ROWID DESC LIMIT 5", (user_id,))
        rows = c.fetchall()
        conn.close()
        if rows:
            msg = "\U0001F4D1 Your Last Estimates:\n"
            for r in rows:
                msg += f"- Age: {r[0]}, Exp: {2024 - r[1]}y, Car: {r[2]}, Eng: {r[3]}cc, Fuel: {r[4]}, Own: {r[5]}, EUR {r[6]}\n"
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("No history found.")
        return

    if text == "\U0001F4A1 FAQ":
        keyboard = [[InlineKeyboardButton(topic, callback_data=topic)] for topic in faq_data]
        keyboard.append([InlineKeyboardButton("Back to menu", callback_data="back_to_menu")])
        await update.message.reply_text("Choose a topic:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if step == "faq":
        return

    if text == "\U0001F4C4 Estimate Insurance":
        user_data["step"] = "age"
        await update.message.reply_text("1️⃣ Your age:")
        return

    try:
        if step == "age":
            user_data["age"] = int(text)
            user_data["step"] = "license_year"
            await update.message.reply_text("2️⃣ What year did you get your driving license?")
        elif step == "license_year":
            user_data["license_year"] = int(text)
            user_data["step"] = "car_year"
            await update.message.reply_text("3️⃣ Car year (e.g. 2015):")
        elif step == "car_year":
            user_data["car_year"] = int(text)
            user_data["step"] = "engine"
            await update.message.reply_text("4️⃣ Engine size in cc (e.g. 1600):")
        elif step == "engine":
            user_data["engine"] = int(text)
            user_data["step"] = "fuel"
            await update.message.reply_text("5️⃣ Fuel type (Petrol / Diesel / Electric / Hybrid):")
        elif step == "fuel":
            user_data["fuel"] = text
            user_data["step"] = "owners"
            await update.message.reply_text("6️⃣ How many previous owners?")
        elif step == "owners":
            user_data["owners"] = int(text)

            age = user_data['age']
            experience = 2024 - user_data['license_year']
            car_year = user_data['car_year']
            engine = user_data['engine']
            fuel = user_data['fuel']
            owners = user_data['owners']

            base = 1000
            if age < 25:
                base += 500
            if experience < 2:
                base += 400
            if engine > 1800:
                base += 250
            if fuel.lower() == "diesel":
                base += 100
            elif fuel.lower() == "electric":
                base -= 150
            elif fuel.lower() == "hybrid":
                base -= 100
            if owners > 3:
                base += 200
            if 2024 - car_year > 10:
                base += 150

            conn = sqlite3.connect("insurance.db")
            c = conn.cursor()
            c.execute("INSERT INTO insurance_requests VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (user_id, age, user_data['license_year'], car_year, engine, fuel, owners, base))
            conn.commit()
            conn.close()

            await update.message.reply_text(f"""
✅ Estimated Annual Insurance:

• Driver Age: {age}
• Driving Experience: {experience} years
• Car Year: {car_year}
• Engine: {engine}cc
• Fuel: {fuel}
• Owners: {owners}

💸 Estimated Insurance: EUR {base}/year

(This is a simulated estimate based on public insurance trends in Ireland.)
""")
            pdf_filename = generate_pdf(user_id, user_data, base)
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("\U0001F4C4 Download PDF", callback_data="download_pdf")]
            ])
            await update.message.reply_text("You can also download the result as a PDF:", reply_markup=keyboard)

            user_states[user_id]["step"] = None
        else:
            await update.message.reply_text("Please select an option from the menu using /start.")
    except ValueError:
        await update.message.reply_text("❗ Please enter a valid number.")

# === INLINE FAQ CALLBACK ===
async def handle_faq_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "back_to_menu":
        await start(update, context)
    elif query.data in faq_data:
        await query.message.reply_text(faq_data[query.data])

# === APP INIT ===
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_callback))
app.add_handler(CallbackQueryHandler(handle_faq_callback))

print("AI Car Check Bot is running...")
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
app.run_polling()
