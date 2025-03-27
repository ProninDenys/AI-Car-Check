# 🤖 AI Car Check

AI Car Check is a smart and helpful Telegram bot designed for drivers in Ireland 🇮🇪. It helps with:
- Estimating car insurance costs
- Tracking and planning vehicle maintenance
- Providing key information for new drivers, car buyers, and car owners
- (Coming soon) Checking vehicle history by registration number

It offers a clean and simple experience through a Telegram chat interface with intuitive button-based interaction.

---

## ✨ Features

- 🚗 **Estimate Insurance**: Get an approximate annual insurance cost based on car and driver details
- 🛠 **Service & Maintenance**: Get upcoming maintenance reminders based on mileage
- 🧾 **Insurance & Service History**: See the last 3 calculations and reports
- 📚 **FAQ**: Useful legal and practical info for motorists in Ireland
- 🔄 Restart conversation easily with a button
- ✅ PDF insurance report download

---

## 🚗 Insurance Estimation Logic

The bot estimates annual insurance based on the following inputs:

- **Driver Age**
- **Driving Experience** (from license year)
- **Car Year**
- **Engine Size (cc)**
- **Fuel Type** (Petrol / Diesel / Electric / Hybrid)
- **Number of Previous Owners**

A weighted formula simulates Irish market pricing for educational use only (not official quotes).

---

## 🛠 Maintenance Logic

The user inputs:
- **Car brand & model**
- **Year of manufacture**
- **Current mileage** (km or miles)
- **Fuel type**

The bot shows only upcoming recommendations based on standard service schedules (oil change, timing belt, etc.).

---

## 📦 Tech Stack

- `Python`
- `python-telegram-bot`
- `SQLite` (for user history)
- `dotenv` (env vars)
- `Render.com` (cloud deployment)
- `ReportLab` (PDF generation)

---

## 📲 How to Use

1. Open the bot on Telegram: [@autocheckai_bot](https://t.me/autocheckai_bot)
2. Tap `/start` to begin
3. Choose:
   - "🚗 Check Car by Reg Number" (coming soon)
   - "📄 Estimate Insurance"
   - "🛠 Service & Maintenance"
   - "📚 FAQ" for car-related info in Ireland

---

## 🧠 Status

This is an MVP project actively evolving with user feedback. API integration and expanded features coming soon.