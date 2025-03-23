import os
import openai
import tempfile
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from docx import Document

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

user_states = {}

# ======== ФУНКЦИЯ ГЕНЕРАЦИИ PDF и DOCX ========
def generate_files(resume_text):
    # === PDF ===
    pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    text = c.beginText(50, height - 50)
    text.setFont("Helvetica", 12)
    text.setFillColor(colors.darkblue)

    for line in resume_text.split('\n'):
        if line.strip().startswith("###"):
            text.setFont("Helvetica-Bold", 13)
            text.setFillColor(colors.black)
        elif line.strip().startswith("##"):
            text.setFont("Helvetica-Bold", 15)
            text.setFillColor(colors.darkred)
        elif line.strip().startswith("#"):
            text.setFont("Helvetica-Bold", 16)
            text.setFillColor(colors.darkblue)
        else:
            text.setFont("Helvetica", 12)
            text.setFillColor(colors.black)
        text.textLine(line.strip())

    c.drawText(text)
    c.save()

    # === DOCX ===
    docx_path = tempfile.NamedTemporaryFile(delete=False, suffix=".docx").name
    doc = Document()
    for line in resume_text.split('\n'):
        doc.add_paragraph(line)
    doc.save(docx_path)

    return pdf_path, docx_path

# ======== СТАРТ с КНОПКАМИ ========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["✍️ New Resume", "📄 My Last Resume"],
        ["💡 LinkedIn Boost", "🎯 ATS Scan"],
        ["📤 Share My Resume", "🌐 Switch Language"],
        ["💬 Help & Tips"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "👋 Welcome to AI Job Assistant!\n\nSelect an option below to begin 👇",
        reply_markup=reply_markup
    )
    user_states[update.effective_user.id] = {'step': None}

# ======== ГЛАВНАЯ ЛОГИКА БОТА ========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = user_states.get(user_id, {})
    step = user_data.get('step')

    if update.message.text == "✍️ New Resume":
        user_data['step'] = 'name'
        await update.message.reply_text("Let's create your resume!\nPlease enter your full name:")
        return
    elif update.message.text == "📄 My Last Resume":
        await update.message.reply_text("❌ Sorry, this feature is coming soon!")
        return
    elif update.message.text == "💡 LinkedIn Boost":
        await update.message.reply_text("🚀 Tip: Add action words like 'improved', 'led', 'optimized' in your resume!")
        return
    elif update.message.text == "🎯 ATS Scan":
        await update.message.reply_text("🧠 Coming soon: scan your resume for ATS-compatibility.")
        return
    elif update.message.text == "📤 Share My Resume":
        await update.message.reply_text("🔗 Tip: Export and send your resume on LinkedIn or email.")
        return
    elif update.message.text == "🌐 Switch Language":
        await update.message.reply_text("🌍 Language switching feature is in development.")
        return
    elif update.message.text == "💬 Help & Tips":
        await update.message.reply_text("🛠 Use '✍️ New Resume' to start. Add relevant skills and clear experience. We'll handle the rest!")
        return

    if step == 'name':
        user_data['name'] = update.message.text
        user_data['step'] = 'position'
        await update.message.reply_text("What position are you applying for?")
    elif step == 'position':
        user_data['position'] = update.message.text
        user_data['step'] = 'experience'
        await update.message.reply_text("Describe your work experience:")
    elif step == 'experience':
        user_data['experience'] = update.message.text
        user_data['step'] = 'skills'
        await update.message.reply_text("List your key skills:")
    elif step == 'skills':
        user_data['skills'] = update.message.text
        await update.message.reply_text("⏳ Generating your resume...")

        # === PROMPT С WOW-ЭФФЕКТОМ ===
        prompt = f"""
Create a standout resume for the following person that will capture the attention of recruiters. 
Structure it with the following sections: Name, Job Title, Summary, Experience, Skills, and a unique \"What Makes Me Stand Out\" section.
Use dynamic and confident language, highlight achievements, soft skills, and make it ATS-friendly.
Pretend it's written for a top-level job application (Google, Meta, Amazon).

Name: {user_data['name']}
Position: {user_data['position']}
Experience: {user_data['experience']}
Skills: {user_data['skills']}
"""

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )

        resume_text = response.choices[0].message.content
        pdf_path, docx_path = generate_files(resume_text)

        await update.message.reply_text("✅ Resume is ready! Download below:")
        await update.message.reply_document(open(pdf_path, "rb"), filename="resume.pdf")
        await update.message.reply_document(open(docx_path, "rb"), filename="resume.docx")

        user_states.pop(user_id, None)

    else:
        await update.message.reply_text("Type /start to begin or click ✍️ New Resume.")

# ======== ЗАПУСК БОТА ========
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🤖 Bot is running...")
app.run_polling()