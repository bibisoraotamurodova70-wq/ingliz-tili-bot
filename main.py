import os
import json
import threading
import time
import random
import requests
import telebot
from flask import Flask, request
from deep_translator import GoogleTranslator

# 1. BOT PARAMETRLARI
API_TOKEN = '8972113004:AAHhJnR6bODO7-CpYqAnFXwrtiiyWR2x7Io'
GROUP_CHAT_ID = '@testlar_bazasi_ingiliz'   

RENDER_URL = "https://ingiliz-tili-bot-ypms.onrender.com" 

bot = telebot.TeleBot(API_TOKEN)
translator = GoogleTranslator(source='en', target='uz')
app = Flask(__name__)

user_scores = {}
poll_database = {}  
test_counter = 0  

fake_answers = [
    "olma", "kitob", "uy", "mashina", "yugurmoq", "baxtli", "sovuq", "issiq", 
    "yozmoq", "suv", "non", "shahar", "yaxshi", "yomon", "katta", "kichik",
    "stul", "stol", "deraza", "eshik", "maktab", "o'qituvchi", "o'quvchi", "ruchka",
    "daftar", "telefon", "kompyuter", "soat", "kalit", "sumka", "pul", "hamyon",
    "nonushta", "tushlik", "kechki ovqat", "sut", "choy", "kofe", "shakar", "tuz",
    "gosht", "baliq", "guruch", "sabzi", "kartoshka", "piyoz", "meva", "sabzavot",
    "sariyog", "pishloq", "tuxum", "asal", "sharbat", "muzqaymoq",
    "daraxt", "gul", "ot", "barg", "osmon", "quyosh", "oy", "yulduz",
    "bulut", "yomg_ir", "qor", "shamol", "havo", "yer", "tosh", "qum",
    "daryo", "kol", "deniz", "okean", "tog", "vodiydan", "ormon", "bog",
    "ota", "ona", "aka", "uka", "opa", "singil", "dost", "bola",
    "odam", "erkak", "ayol", "qoshni", "shifokor", "haydovchi", "muhandis", "asbob",
    "kocha", "bino", "dokon", "bozor", "shifoxona", "dorixona", "mehmonxona", "bekat",
    "aeroport", "vokzal", "zavod", "idora", "teatr", "muzey", "park", "guruh",
    "it", "mushuk", "sigir", "qoy", "tovuq", "qush",
    "sher", "ayiq", "bori", "tulki", "quyon", "sichqon", "fil", "maymun",
    "kiyim", "koylak", "shim", "poyabzal", "shlyapa", "qolqop", "kozoynak", "uzuk",
    "bosh", "koz", "quloq", "burun", "ogiz", "tish", "qol", "oyoq",
    "yurak", "soch", "yuz", "boyin", "yona", "orqa", "qorin", "tana",
    "yurmoq", "kelmoq", "ketmoq", "otirmoq", "turmoq", "uxlamoq", "uygonmoq", "kulmoq",
    "yiglamoq", "gapirmoq", "tinglamoq", "kormoq", "eshitmoq", "oylamoq", "bilmoq", "tushunmoq",
    "ochmoq", "yopmoq", "olmoq", "bermoq", "sotmoq", "sotib olmoq", "tuzatmoq", "sindirmoq",
    "chizmoq", "boyamoq", "yuvmoq", "tozalamoq", "pishirmoq", "yemoq", "ichmoq", "sakramoq",
    "gozal", "xunuk", "aqlli", "ahmoq", "kuchli", "kuchsiz", "boy", "kambagal",
    "yosh", "eski", "yangi", "chaqqon", "sekin", "tez", "ogir", "yengil",
    "toza", "kir", "shirin", "achchiq", "nordon", "shor", "arzon", "qimmat",
    "oson", "qiyin", "togri", "notogri", "uzun", "kalta", "keng", "tor"
]

def get_random_word():
    try:
        response = requests.get("https://random-word-api.herokuapp.com/word?number=1")
        if response.status_code == 200:
            return response.json()[0].capitalize()
    except:
        return None

# REYTING MATNI
def get_leaderboard_text():
    if not user_scores:
        return "📊 Hozircha guruhda hech kim to'g'ri javob berib ball to'plamadi."
    sorted_users = sorted(user_scores.values(), key=lambda x: x['score'], reverse=True)
    leaderboard_text = "📊 **Guruhdagi eng bilimdonlar reytingi (Top 20):**\n\n"
    medals = {1: "🥇 1-o'rin", 2: "🥈 2-o'rin", 3: "🥉 3-o'rin"}
    for index, user in enumerate(sorted_users[:20], start=1):
        place_text = medals.get(index, f"🔹 {index}-o'rin")
        leaderboard_text += f"{place_text}: {user['name']} — {user['score']} ball\n"
    return leaderboard_text

# 2. WEBHOOK ORQALI KELADIGAN HAR QANDAY SIGNALNI TO'G'RIDAN-TO'G'RI O'QISH
@app.route(f"/{API_TOKEN}", methods=['POST'])
def get_message():
    global user_scores
    try:
        data = request.get_json()
        if not data:
            return "!", 200
            
        # OVOZ BERISH SIGNALI KELSA (Kafolatlangan qism)
        if "poll_answer" in data:
            poll_answer = data["poll_answer"]
            poll_id = poll_answer["poll_id"]
            user_info = poll_answer["user"]
            user_id = user_info["id"]
            
            first_name = user_info.get("first_name", "Foydalanuvchi")
            last_name = user_info.get("last_name", "")
            full_name = f"{first_name} {last_name}".strip()
            
            selected_options = poll_answer.get("option_ids", [])
            
            if poll_id in poll_database and selected_options:
                correct_id = poll_database[poll_id]
                # Agar foydalanuvchi to'g'ri variantni tanlagan bo'lsa
                if selected_options[0] == correct_id:
                    if user_id not in user_scores:
                        user_scores[user_id] = {"name": full_name, "score": 0}
                    user_scores[user_id]["score"] += 1
                    print(f"🔥 [FLASK BALL] {full_name} ball oldi! Jami: {user_scores[user_id]['score']}")

        # MATNLI XABARLAR KELSA (/reyting kabi komandalar)
        elif "message" in data:
            update = telebot.types.Update.de_json(data)
            bot.process_new_updates([update])
            
    except Exception as e:
        print(f"Webhook ma'lumotida xatolik: {e}")
    return "!", 200

@app.route("/", methods=['GET'])
def index():
    return "Bot 100% barqaror rejimda ishlamoqda!", 200

# 3. /REYTING BUYRUG'I
@bot.message_handler(commands=['reyting'])
def send_leaderboard(message):
    try:
        text = get_leaderboard_text()
        bot.reply_to(message, text, parse_mode="Markdown")
    except Exception as e:
        print(f"Reyting jo'natishda xato: {e}")

# 4. ASOSIY TEST TASHLOVCHI TSIKL
def test_sending_loop():
    global test_counter, poll_database
    time.sleep(5)  
    print("Test yuborish oqimi ishga tushdi...")
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
            correct_index = options.index(correct_uz)
            
            # GURUHGA TEST TASHLOVCHI
            group_poll = bot.send_poll(
                chat_id=GROUP_CHAT_ID,
                question=word,
                options=options,
                type='quiz',
                correct_option_id=correct_index,
                is_anonymous=False
            )
            poll_database[group_poll.poll.id] = correct_index
            
            test_counter += 1
            print(f"Test #{test_counter} muvaffaqiyatli guruhga chiqdi.")
            
            # REKLAMA
            if test_counter % 3 == 0 and test_counter < 30:
                time.sleep(1)
                bot.send_message(GROUP_CHAT_ID, "📢 **Do'stlaringizni ham guruhga taklif qiling va bilimdonlar turnirida g'olib bo'ling!**")
            
            # TURNIR YAKUNI
            if test_counter >= 30:
                time.sleep(20) 
                
                reyting_matni = "🔔 **30 ta test yakunlandi!**\n\n" + get_leaderboard_text()
                bot.send_message(GROUP_CHAT_ID, reyting_matni, parse_mode="Markdown")
                bot.send_message(GROUP_CHAT_ID, "⏳ **Navbatdagi turnir 15 daqiqadan so'ng boshlanadi.**")
                
                poll_database.clear()
                test_counter = 0
                time.sleep(900)  # 15 daqiqa dam
                
                bot.send_message(GROUP_CHAT_ID, "🚀 **Yangi turnir boshlandi! Ilk testlar yo'lda...**")
                continue
                
            time.sleep(60)  # Har 5 daqiqa
            
        except Exception as e:
            print(f"Test yuborishda xatolik: {e}")
            time.sleep(15)

if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(1)
    # Telegramga webhook ulash (Barcha signallarni birga olish)
    bot.set_webhook(url=f"{RENDER_URL}/{API_TOKEN}", allowed_updates=['message', 'poll_answer'])
    print("Yangi Mustahkam Webhook o'rnatildi!")
    
    threading.Thread(target=test_sending_loop, daemon=True).start()
    
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
