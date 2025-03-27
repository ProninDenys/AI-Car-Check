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
c.execute('''CREATE TABLE IF NOT EXISTS maintenance_requests (
    user_id INTEGER,
    brand TEXT,
    model TEXT,
    year TEXT,
    mileage INTEGER,
    unit TEXT,
    fuel TEXT
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

# === MAINTENANCE REPORT ===
def get_maintenance_recommendations(mileage):
    checklist = [
        (15000, "Oil & Filter Change (every 10–15k km)"),
        (30000, "Air Filter Change"),
        (60000, "Spark Plugs Replacement"),
        (90000, "Timing Belt Inspection"),
        (120000, "Spark Plugs Replacement again"),
        (150000, "Suspension & Steering Inspection"),
        (180000, "Timing Belt Check"),
        (180000, "Spark Plugs again"),
        (210000, "Air Filter Change"),
        (240000, "Spark Plugs Replacement again"),
        (270000, "Timing Belt Inspection"),
        (300000, "Oil & Filter Change"),
        (330000, "Timing Belt Inspection"),
        (360000, "Spark Plugs Replacement")
    ]
    return [(km, task) for km, task in checklist if km > mileage]

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

# === START ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = {"step": None}
    keyboard = [["\U0001F4C4 Estimate Insurance"],
                ["\U0001F527 Service & Maintenance"],
                ["\U0001F4D1 Insurance History"],
                ["\U0001F4DC Service History"],
                ["\U0001F504 Start Over"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Welcome to AutoCheck AI!\n\nChoose a feature below to begin:", reply_markup=reply_markup)

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

    if text == "\U0001F4D1 Insurance History":
        conn = sqlite3.connect("insurance.db")
        c = conn.cursor()
        c.execute("SELECT age, license_year, car_year, engine, fuel, owners, estimate FROM insurance_requests WHERE user_id=? ORDER BY ROWID DESC LIMIT 3", (user_id,))
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

    if text == "\U0001F4DC Service History":
        conn = sqlite3.connect("insurance.db")
        c = conn.cursor()
        c.execute("SELECT brand, model, year, mileage, unit, fuel FROM maintenance_requests WHERE user_id=? ORDER BY ROWID DESC LIMIT 3", (user_id,))
        rows = c.fetchall()
        conn.close()
        if rows:
            for r in rows:
                brand, model, year, mileage, unit, fuel = r
                if unit.lower() == "miles":
                    mileage = round(mileage * 1.6)
                report = f"\n🔧 {brand} {model} ({year}) — {mileage} km — {fuel}\n"
                upcoming = get_maintenance_recommendations(mileage)
                if upcoming:
                    report += "\n📍 Upcoming recommendations:\n"
                    for km, task in upcoming:
                        report += f"⚠️ {km} km — {task}\n"
                else:
                    report += "\n✅ No further maintenance needed.\n"
                await update.message.reply_text(report)
        else:
            await update.message.reply_text("No service history found.")
        return

    if text == "\U0001F4C4 Estimate Insurance":
        user_data["step"] = "age"
        await update.message.reply_text("1️⃣ Your age:")
        return

    if text == "\U0001F527 Service & Maintenance":
        user_data["step"] = "brand"
        await update.message.reply_text("Enter your car brand (e.g. Toyota):")
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
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("\U0001F4C4 Download PDF", callback_data="download_pdf")]])
            await update.message.reply_text("You can also download the result as a PDF:", reply_markup=keyboard)
            user_states[user_id]["step"] = None

        elif step == "brand":
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
            user_data["step"] = "fuel_type"
            await update.message.reply_text("Fuel type: Petrol / Diesel / Electric / Hybrid")
        elif step == "fuel_type":
            user_data["fuel"] = text
            brand = user_data["brand"]
            model = user_data["model"]
            year = user_data["year"]
            mileage = user_data["mileage"]
            unit = user_data["unit"]
            fuel = user_data["fuel"]

            if unit.lower() == "miles":
                mileage = round(mileage * 1.6)

            recommendations = get_maintenance_recommendations(mileage)
            report = f"\n🔧 Maintenance Recommendations for {brand} {model} ({year}) — {mileage} km, {fuel}\n"
            if recommendations:
                report += "\n📍 Upcoming recommendations:\n"
                for km, task in recommendations:
                    report += f"⚠️ {km} km — {task}\n"
            else:
                report += "\n✅ No upcoming maintenance needed."

            conn = sqlite3.connect("insurance.db")
            c = conn.cursor()
            c.execute("INSERT INTO maintenance_requests VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (user_id, brand, model, year, mileage, unit, fuel))
            conn.commit()
            conn.close()

            await update.message.reply_text(report)
            user_states[user_id]["step"] = None

    except ValueError:
        await update.message.reply_text("❗ Please enter a valid number.")

# === INIT ===
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_callback))

print("AI Car Check Bot is running...")
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
app.run_polling()