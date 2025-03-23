# 🚗 AI Car Check

**AI Car Check** is a smart and powerful Telegram bot that helps users in **Ireland** check vehicle history and estimate insurance and road tax based on registration number and car parameters.

It’s designed for drivers, buyers, and car owners who want quick insights before buying or insuring a vehicle.

---

## ✨ Features

- Check vehicle by **registration number** (accidents, NCT, owners, etc.)
- Estimate **insurance cost** based on driver profile and car details
- Estimate **Road Tax** using engine size, fuel type, and year
- Telegram-based step-by-step flow with interactive buttons
- Future support for real data via **MotorCheck API**, **data.gov.ie**, and **gov.ie**

---

## 🧰 Tech Stack

- `Python`
- `python-telegram-bot`
- `dotenv` (for environment variables)
- `Render.com` for 24/7 deployment
- *(optional in future)*: `MotorCheck API`, `data.gov.ie`, `gov.ie`

---

## 🚀 Local Setup

```bash
git clone https://github.com/ProninDenys/ai-car-check-bot.git
cd ai-car-check-bot
python -m venv venv
source venv/bin/activate  
pip install -r requirements.txt