import os
import sqlite3
import threading
import time
import random
import requests
import telebot
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from deep_translator import GoogleTranslator

# 1. PARAMETRLAR
API_TOKEN = '8972113004:AAHhJnR6bODO7-CpYqAnFXwrtiiyWR2x7Io'
GROUP_CHAT_ID = '@testlar_bazasi_ingiliz'   
RENDER_URL = "https://ingiliz-tili-bot-ypms.onrender.com" 

bot = telebot.TeleBot(API_TOKEN)
translator = GoogleTranslator(source='en', target='uz')
app = Flask(__name__)

DB_FILE = "bot_database.db"

# 2. BAZANI SOZLACH
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            score INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_tests (
            message_id INTEGER PRIMARY KEY,
            correct_answer TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS solved_tests (
            user_id INTEGER,
            message_id INTEGER,
            PRIMARY KEY (user_id, message_id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def add_score(user_id, name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT score FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        new_score = row[0] + 1
        cursor.execute("UPDATE users SET name = ?, score = ? WHERE user_id = ?", (name, new_score, user_id))
    else:
        new_score = 1
        cursor.execute("INSERT INTO users (user_id, name, score) VALUES (?, ?, ?)", (user_id, name, new_score))
    conn.commit()
    conn.close()
    return new_score

def get_leaderboard_text():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, score FROM users ORDER BY score DESC LIMIT 20")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return "📊 Hozircha guruhda hech kim to'g'ri javob berib ball to'plamadi."
        
    leaderboard_text = "📊 **Guruhdagi eng bilimdonlar reytingi (Top 20):**\n\n"
    medals = {1: "🥇 1-o'rin", 2: "🥈 2-o'rin", 3: "🥉 3-o'rin"}
    for index, (name, score) in enumerate(rows, start=1):
        place_text = medals.get(index, f"🔹 {index}-o'rin")
        leaderboard_text += f"{place_text}: {name} — {score} ball\n"
    return leaderboard_text

fake_answers = [
    "olma", "kitob", "uy", "mashina", "yugurmoq", "baxtli", "sovuq", "issiq", "suv", "non", "shahar",
    "stul", "stol", "deraza", "eshik", "maktab", "ruchka", "daftar", "telefon", "kompyuter", "soat"
]

def get_random_word():
    try:
        response = requests.get("https://random-word-api.herokuapp.com/word?number=1")
        if response.status_code == 200:
            return response.json()[0].capitalize()
    except:
        return None

# 3. WEBHOOK SHLYUZI
@app.route(f"/{API_TOKEN}", methods=['POST'])
def get_message():
    try:
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return "!", 200
    except Exception as e:
        print(f"Webhook xatosi: {e}")
    return "!", 200

@app.route("/", methods=['GET'])
def index():
    return "Bot 1 daqiqalik rejimda faol!", 200

# 4. CALLBACK HANDLER
@bot.callback_query_handler(func=lambda call: call.data.startswith("ans_"))
def handle_answer(call):
    try:
        user_id = call.from_user.id
        first_name = call.from_user.first_name if call.from_user.first_name else "Bilimdon"
        last_name = call.from_user.last_name if call.from_user.last_name else ""
        full_name = f"{first_name} {last_name}".strip()
        
        message_id = call.message.message_id
        selected_answer = call.data.split("ans_")[1]
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM solved_tests WHERE user_id = ? AND message_id = ?", (user_id, message_id))
        already_solved = cursor.fetchone()
        
        if already_solved:
            bot.answer_callback_query(call.id, "⚠️ Siz bu testga javob berib bo'lgansiz!", show_alert=True)
            conn.close()
            return
            
        cursor.execute("SELECT correct_answer FROM active_tests WHERE message_id = ?", (message_id,))
        row = cursor.fetchone()
        
        if not row:
            bot.answer_callback_query(call.id, "⚠️ Bu test muddati tugagan yoki eskirgan!")
            conn.close()
            return
            
        correct_answer = row[0]
        
        if selected_answer == correct_answer:
            cursor.execute("INSERT INTO solved_tests (user_id, message_id) VALUES (?, ?)", (user_id, message_id))
            conn.commit()
            conn.close()
            
            current_score = add_score(user_id, full_name)
            bot.answer_callback_query(call.id, f"🎉 To'g'ri topdingiz!\nSizning jami ballingiz: {current_score} taga yetdi.", show_alert=True)
        else:
            conn.close()
            bot.answer_callback_query(call.id, "❌ Noto'g'ri javob! Boshqa variantni tanlab ko'ring.", show_alert=False)
            
    except Exception as e:
        print(f"Callback xatosi: {e}")

# 5. REYTING BUYRUG'I
@bot.message_handler(commands=['reyting'])
def send_leaderboard(message):
    try:
        text = get_leaderboard_text()
        bot.reply_to(message, text, parse_mode="Markdown")
    except Exception as e:
        print(f"Reyting xatosi: {e}")

# 6. ASOSIY TEST TSIKLI (1 DAQIQA REJIMIGA O'TKAZILDI)
def test_sending_loop():
    time.sleep(5)
    test_counter = 0
    print("1 daqiqalik test tizimi ishga tushdi...")
    while True:
        try:
            word = get_random_word()
            if not word:
                time.sleep(10)
                continue
                
            correct_uz = translator.translate(word).lower()
            if word.lower() == correct_uz:
                continue
                
            wrong_options = random.sample(fake_answers, 3)
            if correct_uz in wrong_options:
                continue
                
            options = wrong_options + [correct_uz]
            random.shuffle(options)
            
            markup = InlineKeyboardMarkup(row_width=2)
            buttons = [InlineKeyboardButton(text=opt.capitalize(), callback_data=f"ans_{opt}") for opt in options]
            markup.add(*buttons)
            
            msg = bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=f"🇬🇧 **{word}** — so'zining to'g'ri tarjimasini toping:",
                reply_markup=markup,
                parse_mode="Markdown"
            )
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO active_tests (message_id, correct_answer) VALUES (?, ?)", (msg.message_id, correct_uz))
            conn.commit()
            conn.close()
            
            test_counter += 1
            print(f"Test #{test_counter} guruhga yuborildi.")
            
            if test_counter >= 30:
                time.sleep(30)
                reyting_matni = "🔔 **30 ta test yakunlandi!**\n\n" + get_leaderboard_text()
                bot.send_message(GROUP_CHAT_ID, reyting_matni, parse_mode="Markdown")
                
                test_counter = 0
                time.sleep(900)  # 15 daqiqa tanaffus
                bot.send_message(GROUP_CHAT_ID, "🚀 **Yangi turnir boshlandi! Ilk savollar yo'lda...**")
                continue
                
            # SHU JOYI 300 DAN 60 GA O'ZGARTIRILDI (1 DAQIQA)
            time.sleep(60) 
            
        except Exception as e:
            print(f"Tsikl xatosi: {e}")
            time.sleep(15)

if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=f"{RENDER_URL}/{API_TOKEN}", allowed_updates=['message', 'callback_query'])
    print("Webhook muvaffaqiyatli sozlandi!")
    
    threading.Thread(target=test_sending_loop, daemon=True).start()
    
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
