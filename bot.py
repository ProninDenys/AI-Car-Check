import os
import random
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
user_states = {}

# ======== START COMMAND ========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Check Car by Reg Number"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Welcome to AI Car Check — your smart auto agent in Ireland!\n\nTap the button below to start.",
        reply_markup=reply_markup
    )
    user_states[update.effective_user.id] = {"step": None}

# ======== MESSAGE HANDLER ========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = user_states.get(user_id, {})
    step = user_data.get("step")

    text = update.message.text

    if text == "Check Car by Reg Number":
        user_data["step"] = "reg"
        await update.message.reply_text("Please enter the vehicle's registration number (e.g. 12D34567):")
        return

    if step == "reg":
        user_data["reg"] = text
        user_data["step"] = "year"
        await update.message.reply_text("Enter year of manufacture (e.g. 2015):")
    elif step == "year":
        user_data["year"] = text
        user_data["step"] = "engine"
        await update.message.reply_text("Enter engine size in cc (e.g. 1598):")
    elif step == "engine":
        user_data["engine"] = text
        user_data["step"] = "mileage"
        await update.message.reply_text("Enter mileage in km (e.g. 120000):")
    elif step == "mileage":
        user_data["mileage"] = text
        user_data["step"] = "owners"
        await update.message.reply_text("How many previous owners?:")
    elif step == "owners":
        user_data["owners"] = text
        user_data["step"] = "fuel"
        await update.message.reply_text("Enter fuel type (Petrol/Diesel/Electric):")
    elif step == "fuel":
        user_data["fuel"] = text
        user_data["step"] = "driver_age"
        await update.message.reply_text("Enter your age:")
    elif step == "driver_age":
        user_data["driver_age"] = text
        user_data["step"] = "license_year"
        await update.message.reply_text("Year you got your driving license:")
    elif step == "license_year":
        user_data["license_year"] = text

        # === FAKE REPORT (MVP STUB) ===
        car_reg = user_data['reg']
        fake_accidents = random.choice(["No accidents reported", "1 minor accident in 2019", "Multiple repairs after collision"])
        owners = user_data['owners']
        nct = random.choice(["Valid until Jan 2026", "Expired - needs retest", "Passed in Feb 2024"])
        insurance_est = random.randint(750, 1800)
        road_tax = random.randint(200, 600)

        response = f"""
🚗 Vehicle Report for {car_reg}:

- Year: {user_data['year']}
- Engine: {user_data['engine']}cc
- Mileage: {user_data['mileage']} km
- Fuel Type: {user_data['fuel']}
- Previous Owners: {owners}
- NCT Status: {nct}
- Accident History: {fake_accidents}

💸 Estimated Insurance: €{insurance_est}/year
🧾 Road Tax Estimate: €{road_tax}/year

(This is a demo. Real API integration coming soon.)
"""
        await update.message.reply_text(response)
        user_states.pop(user_id, None)
    else:
        await update.message.reply_text("Please tap /start or use the menu to begin.")

# ======== RUN APP ========
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🚗 AI Car Check Bot is running...")
app.run_polling()
