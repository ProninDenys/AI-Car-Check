import os
import random
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
user_states = {}

# ======== START COMMAND ========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_states:
        user_states[user_id] = {"step": None}

    keyboard = [["🚗 Check Car by Reg Number"], ["📄 Estimate Insurance"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Welcome to AutoCheck AI!\n\nChoose a feature below to begin:",
        reply_markup=reply_markup
    )

# ======== MESSAGE HANDLER ========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_states:
        user_states[user_id] = {"step": None}

    user_data = user_states[user_id]
    step = user_data.get("step")

    if text == "📄 Estimate Insurance":
        user_data["step"] = "age"
        await update.message.reply_text("1️⃣ Your age:")
        return

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

        # === Estimate logic ===
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
        user_states[user_id]["step"] = None
    else:
        await update.message.reply_text("Please select an option from the menu using /start.")

# ======== RUN APP ========
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🚗 AI Car Check Bot is running...")
app.run_polling()
