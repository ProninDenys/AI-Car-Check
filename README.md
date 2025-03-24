# 🤖 AI Car Check

AI Car Check is a smart and helpful Telegram bot that allows users in Ireland 🇮🇪 to:
- Check vehicle history by registration number (coming soon)
- Estimate annual car insurance cost based on car and driver details

It offers a clean and simple experience through a Telegram chat interface with button-based interaction.

---

## ✨ Features

- Two main functions: vehicle check & insurance estimation
- Insurance cost estimate based on public Irish market trends
- Interactive question-based flow
- Easy Telegram integration

---

## 🚗 Insurance Estimation Logic

The bot estimates annual insurance based on the following inputs:

- **Driver Age**
- **Driving Experience** (calculated from license year)
- **Car Year**
- **Engine Size (cc)**
- **Fuel Type** (Petrol / Diesel / Electric / Hybrid)
- **Number of Previous Owners**

A simple weighted formula is used to simulate realistic insurance prices for Ireland. (This is **not** official data, but based on patterns from real quotes.)

---

## 📦 Tech Stack

- `Python`
- `python-telegram-bot`
- `dotenv` (for managing secret keys)
- `Render.com` (for cloud deployment)

---

## 📍 Coming Soon

- Integration with official Irish vehicle APIs (e.g., MotorCheck)
- Full registration number lookup with history, NCT, valuation
- Real-time insurance quote from providers

---

## 📲 How to Use

1. Open the bot on Telegram [@autocheckai_bot](https://t.me/autocheckai_bot)
2. Tap `/start` to begin
3. Choose between “Check Car by Reg Number” or “Estimate Insurance Cost”

---

🧠 This project is in MVP stage. More features coming soon!