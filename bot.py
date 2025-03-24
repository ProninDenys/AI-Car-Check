import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
user_states = {}

# ==== СТАРТ: Главное меню ====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🚗 Estimate Insurance", "🔍 Check Car History (coming soon)"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Welcome to AutoCheck AI!\n\nChoose a feature below to begin:",
        reply_markup=reply_markup
    )
    user_states[update.effective_user.id] = {"step": None}

# ==== ЛОГИКА ====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = user_states.get(user_id, {})
    step = user_data.get("step")
    text = update.message.text

    if text == "🚗 Estimate Insurance":
        user_data["step"] = "age"
        await update.message.reply_text("1️⃣ Your age:")
        return

    elif text == "🔍 Check Car History (coming soon)":
        await update.message.reply_text("⏳ This feature will be available soon.")
        return

    # ==== Сбор данных ====
    if step == "age":
        user_data["age"] = int(text)
        user_data["step"] = "license_year"
        await update.message.reply_text("2️⃣ What year did you get your driving license?")
    elif step == "license_year":
        user_data["license_year"] = int(text)
        user_data["step"] = "car_year"
        await update.message.reply_text("3️⃣ Year of car manufacture:")
    elif step == "car_year":
        user_data["car_year"] = int(text)
        user_data["step"] = "engine_size"
        await update.message.reply_text("4️⃣ Engine size (in cc, e.g. 1600):")
    elif step == "engine_size":
        user_data["engine_size"] = int(text)
        user_data["step"] = "fuel"
        await update.message.reply_text("5️⃣ Fuel type (Petrol / Diesel / Electric):")
    elif step == "fuel":
        user_data["fuel"] = text.lower()
        user_data["step"] = "owners"
        await update.message.reply_text("6️⃣ How many previous owners?")
    elif step == "owners":
        user_data["owners"] = int(text)

        # ==== Расчёт страховки ====
        base_price = 750

        # Возраст водителя
        if user_data["age"] < 25:
            base_price += 400
        elif user_data["age"] < 30:
            base_price += 200
        else:
            base_price += 100

        # Опыт вождения
        driving_years = 2025 - user_data["license_year"]
        if driving_years < 3:
            base_price += 300
        elif driving_years < 5:
            base_price += 150
        else:
            base_price -= 50

        # Возраст машины
        car_age = 2025 - user_data["car_year"]
        if car_age > 15:
            base_price += 200
        elif car_age > 10:
            base_price += 100

        # Объём двигателя
        if user_data["engine_size"] > 2000:
            base_price += 200
        elif user_data["engine_size"] > 1600:
            base_price += 100

        # Тип топлива
        if user_data["fuel"] == "diesel":
            base_price += 50
        elif user_data["fuel"] == "electric":
            base_price -= 100

        # Кол-во владельцев
        if user_data["owners"] >= 3:
            base_price += 100

        total = max(550, base_price)

        await update.message.reply_text(f"""
✅ Estimated Annual Insurance:

• Driver Age: {user_data['age']}
• Driving Experience: {driving_years} years
• Car Year: {user_data['car_year']}
• Engine: {user_data['engine_size']}cc
• Fuel: {user_data['fuel'].capitalize()}
• Owners: {user_data['owners']}

💸 Estimated Insurance: €{total}/year

(This is a simulated estimate based on public insurance trends.)
""")
        user_states.pop(user_id, None)

    else:
        await update.message.reply_text("Please click /start to begin or select an option from the menu.")

# ==== ЗАПУСК ====
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🚗 AutoCheck bot is running...")
app.run_polling()