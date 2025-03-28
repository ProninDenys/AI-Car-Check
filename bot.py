import os
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
def generate_pdf(user_id, data, estimate, maintenance_report=None):
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
    
    if maintenance_report:
        c.drawString(100, 620, "Maintenance Report:")
        c.drawString(100, 600, maintenance_report)
    
    c.save()
    return filename

# === FAQ TEXT ===
faq_data = {
    "Learner Permit": "To get a Learner Permit in Ireland, you must pass the theory test, apply at NDLS.ie, and show proof of ID and address.",
    "New Driver": "Display 'L' plates, follow beginner driving restrictions, and be accompanied if required until fully licensed.",
    "How to buy a car": "Buy from dealer or privately. Always check NCT status, tax, ownership history, and get a receipt.",
    "Registration": "Register at Motor Tax Office or online for imports. You'll need proof of ownership and ID.",
    "Road Tax": "Pay road tax online via motortax.ie. Rates depend on engine size or CO2 emissions.",
    "NCT": "NCT is the car test in Ireland. Book at ncts.ie. Required every 1–2 years based on age.",
    "Required Documents": "You need vehicle logbook, ID, insurance, and roadworthiness certificates."
}

# === MENU ===
def get_main_menu():
    keyboard = [["\U0001F697 Check Car by Reg Number"],
                ["\U0001F4C4 Estimate Insurance"],
                ["\U0001F527 Service & Maintenance"],
                ["\U0001F4D1 Insurance History"],
                ["\U0001F4DC Service History"],
                ["\U0001F504 Start Over"],
                ["\U0001F4A1 FAQ"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# === CALLBACKS ===
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
    elif query.data == "back_to_menu":
        await query.message.reply_text("Returning to menu...", reply_markup=get_main_menu())
    elif query.data in faq_data:
        await query.message.reply_text(faq_data[query.data], reply_markup=get_main_menu())

# === START ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = {"step": None}
    await update.message.reply_text("Welcome to AutoCheck AI!\n\nChoose a feature below to begin:", reply_markup=get_main_menu())

# === MAINTENANCE RECOMMENDATIONS ===
def get_maintenance_recommendations(mileage, fuel):
    checklist = [
    (10000, "Oil & Filter Change"),
    (30000, "Air Filter Replacement"),
    (45000, "Brake Pads Check"),
    (60000, "Spark Plugs Replacement"),
    (75000, "Coolant Level & Battery Check"),
    (90000, "Timing Belt Inspection"),
    (105000, "Brake Fluid Replacement"),
    (120000, "Spark Plugs Replacement Again"),
    (135000, "Fuel Filter Replacement (for Diesel)"),
    (150000, "Suspension & Steering Inspection"),
    (165000, "Transmission Fluid Change"),
    (180000, "Timing Belt Replacement"),
    (195000, "Brake Discs Check"),
    (210000, "Air Filter Replacement"),
    (225000, "Spark Plugs Replacement"),
    (240000, "Engine Mounts Inspection"),
    (255000, "Oil & Filter Change"),
    (270000, "Timing Belt Inspection"),
    (285000, "EGR Valve Cleaning (Diesel)"),
    (300000, "Full Inspection & Emission Check"),
    (315000, "Suspension Check"),
    (330000, "Brake Fluid Inspection"),
    (345000, "Spark Plugs Cleaning (for Diesel)"),
    (360000, "Full Inspection & Emission Check"),
    (375000, "Timing Belt Change (Check Condition)"),
    (390000, "Alternator Check"),
    (405000, "Transmission Fluid Check"),
    (420000, "Coolant Flush"),
    (435000, "Oil & Filter Change"),
    (450000, "Tire Change and Alignment"),
    (465000, "Full Service Inspection"),
    (480000, "Timing Belt Change"),
    (495000, "Suspension & Steering Check"),
    (510000, "EGR Valve Cleaning (Diesel)"),
    (525000, "Full Check-up"),
    (540000, "Brake Fluid Check"),
    (555000, "Engine Mount Inspection"),
    (570000, "Timing Belt Inspection"),
    (585000, "Oil & Filter Change"),
    (600000, "Full Service Inspection"),
    (615000, "Brake Pad Replacement"),
    (630000, "Spark Plugs Cleaning"),
    (645000, "Coolant Flush"),
    (660000, "Transmission Fluid Check"),
    (675000, "Full Inspection & Emission Check"),
    (690000, "Engine Check and Service"),
]

    past = [(km, task) for km, task in checklist if mileage >= km]
    upcoming = [(km, task) for km, task in checklist if mileage < km]

    report = f"🔧 Maintenance for {fuel} — {mileage} km\n\n"

    if past:
        report += "📌 What should have already been done:\n"
        for km, task in past[-5:]:
            report += f"✔️ {km} km — {task}\n"
    else:
        report += "📌 No maintenance history found.\n"

    report += "\n📍 Upcoming recommendations:\n"
    if upcoming:
        for km, task in upcoming[:5]:
            report += f"⚠️ {km} km — {task}\n"
    else:
        report += "✅ No upcoming maintenance needed."

    return report


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
        await update.message.reply_text("Restarted.", reply_markup=get_main_menu())
        return

    if text == "\U0001F4A1 FAQ":
        keyboard = [[InlineKeyboardButton(topic, callback_data=topic)] for topic in faq_data]
        keyboard.append([InlineKeyboardButton("Back to menu", callback_data="back_to_menu")])
        await update.message.reply_text("Choose a topic:", reply_markup=InlineKeyboardMarkup(keyboard))
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
                    # Convert mileage from miles to kilometers
                    mileage = round(mileage * 1.60934)
                recommendations = get_maintenance_recommendations(mileage, fuel)
                report = f"\n🔧 {brand} {model} ({year}) — {mileage} km — {fuel}\n"
                if recommendations:
                    report += "\n📍 Upcoming recommendations:\n"
                    for km, task in recommendations:
                        report += f"⚠️ {km} km — {task}\n"
                else:
                    report += "\n✅ No further maintenance needed."
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
            await update.message.reply_text("2️⃣ Year you got your license:")
        elif step == "license_year":
            user_data["license_year"] = int(text)
            user_data["step"] = "car_year"
            await update.message.reply_text("3️⃣ Car year (e.g. 2015):")
        elif step == "car_year":
            user_data["car_year"] = int(text)
            user_data["step"] = "engine"
            await update.message.reply_text("4️⃣ Engine size (cc):")
        elif step == "engine":
            user_data["engine"] = int(text)
            user_data["step"] = "fuel"
            await update.message.reply_text("5️⃣ Fuel type:")
        elif step == "fuel":
            user_data["fuel"] = text
            user_data["step"] = "owners"
            await update.message.reply_text("6️⃣ Previous owners:")
        elif step == "owners":
            user_data["owners"] = int(text)
            age = user_data['age']
            exp = 2024 - user_data['license_year']
            car_year = user_data['car_year']
            engine = user_data['engine']
            fuel = user_data['fuel']
            owners = user_data['owners']

            base = 1000
            if age < 25: base += 500
            if exp < 2: base += 400
            if engine > 1800: base += 250
            if fuel.lower() == "diesel": base += 100
            elif fuel.lower() == "electric": base -= 150
            elif fuel.lower() == "hybrid": base -= 100
            if owners > 3: base += 200
            if 2024 - car_year > 10: base += 150

            conn = sqlite3.connect("insurance.db")
            c = conn.cursor()
            c.execute("INSERT INTO insurance_requests VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (user_id, age, user_data['license_year'], car_year, engine, fuel, owners, base))
            conn.commit()
            conn.close()

            await update.message.reply_text(f"""
✅ Estimated Annual Insurance:
• Driver Age: {age}
• Experience: {exp} years
• Car Year: {car_year}
• Engine: {engine}cc
• Fuel: {fuel}
• Owners: {owners}

💸 Estimated Insurance: EUR {base}/year
(This is a simulated estimate.)
""")
            pdf_filename = generate_pdf(user_id, user_data, base)
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("\U0001F4C4 Download PDF", callback_data="download_pdf")]])
            await update.message.reply_text("Download your result:", reply_markup=keyboard)
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
            await update.message.reply_text("Enter mileage:")
        elif step == "mileage":
            # Проверка ввода пробега
            try:
                mileage = int(text)
                user_data["mileage"] = mileage
                user_data["step"] = "unit"
                await update.message.reply_text("Mileage unit: km or miles?")
            except ValueError:
                await update.message.reply_text("❗ Please enter a valid number for mileage.")
                return
        elif step == "unit":
            user_data["unit"] = text
            user_data["step"] = "fuel_type"
            await update.message.reply_text("Fuel type: Petrol / Diesel / Electric / Hybrid")
        elif step == "fuel_type":
            user_data["fuel"] = text
            brand = user_data['brand']
            model = user_data['model']
            year = user_data['year']
            mileage = user_data['mileage']
            unit = user_data['unit']
            fuel = user_data['fuel']

            if unit.lower() == "miles":
                mileage = round(mileage * 1.60934)

            conn = sqlite3.connect("insurance.db")
            c = conn.cursor()
            c.execute("INSERT INTO maintenance_requests VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (user_id, brand, model, year, mileage, unit, fuel))
            conn.commit()
            conn.close()

            recommendations = get_maintenance_recommendations(mileage, fuel)
            report = f"\n🔧 Maintenance for {brand} {model} ({year}) — {mileage} km, {fuel}\n"
            if recommendations:
                report += "\n📍 Upcoming recommendations:\n"
                for km, task in recommendations:
                    report += f"⚠️ {km} km — {task}\n"
            else:
                report += "\n✅ No upcoming maintenance needed."

            # Add maintenance report to PDF
            pdf_filename = generate_pdf(user_id, user_data, base, report)
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("\U0001F4C4 Download PDF", callback_data="download_pdf")]])
            await update.message.reply_text(report, reply_markup=keyboard)
            user_states[user_id]["step"] = None

    except ValueError:
        await update.message.reply_text("❗ Enter a valid number.")

# === INIT ===
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_callback))

print("AI Car Check Bot is running...")
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
app.run_polling()