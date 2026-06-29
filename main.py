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
GROUP_CHAT_ID = '@testlar_bazasi_ingiliz'   # Guruh manzili (Kanal olib tashlandi)

# Render'dagi haqiqiy havolangiz
RENDER_URL = "https://ingiliz-tili-bot-ypms.onrender.com" 

bot = telebot.TeleBot(API_TOKEN)
translator = GoogleTranslator(source='en', target='uz')
app = Flask(__name__)

user_scores = {}
poll_database = {}  
test_counter = 0  

# Chalg'ituvchi variantlar ro'yxati
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

# REYTING MATNI (TOP 20)
def get_leaderboard_text():
    if not user_scores:
        return "📊 Hozircha guruhda hech kim ball to'plamadi."
    sorted_users = sorted(user_scores.values(), key=lambda x: x['score'], reverse=True)
    leaderboard_text = "📊 **Guruhdagi eng bilimdonlar reytingi (Top 20):**\n\n"
    medals = {1: "🥇 1-o'rin", 2: "🥈 2-o'rin", 3: "🥉 3-o'rin"}
    for index, user in enumerate(sorted_users[:20], start=1):
        place_text = medals.get(index, f"🔹 {index}-o'rin")
        leaderboard_text += f"{place_text}: {user['name']} — {user['score']} ball\n"
    return leaderboard_text

# 2. WEBHOOK SO'ROVLARINI QABUL QILISH
@app.route(f"/{API_TOKEN}", methods=['POST'])
def get_message():
    try:
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return "!", 200
    except Exception as e:
        print(f"Update qayta ishlashda xato: {e}")
    return "!", 200

@app.route("/", methods=['GET'])
def index():
    return "Bot muvaffaqiyatli guruh rejimida ishlamoqda!", 200

# 3. OVOZ BERGAN FOYDALANUVCHILARNI RO'YXATGA OLISH
@bot.poll_answer_handler()
def handle_poll_answer(poll_answer):
    try:
        poll_id = poll_answer.poll_id
        user_id = poll_answer.user.id
        
        first_name = poll_answer.user.first_name if poll_answer.user.first_name else "Foydalanuvchi"
        last_name = poll_answer.user.last_name if poll_answer.user.last_name else ""
        full_name = f"{first_name} {last_name}".strip()
        
        if poll_id in poll_database:
            correct_id = poll_database[poll_id]
            user_answers = poll_answer.option_ids
            
            if user_answers and user_answers[0] == correct_id:
                if user_id not in user_scores:
                    user_scores[user_id] = {"name": full_name, "score": 0}
                user_scores[user_id]["score"] += 1
                print(f"[GURUH BALL] {full_name} to'g'ri topdi! Jami: {user_scores[user_id]['score']}")
    except Exception as e:
        print(f"Poll handlerda xato: {e}")

# 4. /REYTING BUYRUG'I
@bot.message_handler(commands=['reyting'])
def send_leaderboard(message):
    try:
        text = get_leaderboard_text()
        bot.reply_to(message, text, parse_mode="Markdown")
        print("[REYTING] Reyting muvaffaqiyatli guruhga yuborildi.")
    except Exception as e:
        print(f"Reyting jo'natishda xato: {e}")

# 5. ASOSIY TEST TASHLOVCHI TSIKL
def test_sending_loop():
    global test_counter, poll_database
    time.sleep(5)  
    print("Test yuborish oqimi fonda muvaffaqiyatli ish boshladi...")
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
            
            # FAQAT GURUHGA TEST CHIQARISH
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
            print(f"Test #{test_counter} guruhga yuborildi.")
            
            # REKLAMA CHIQARISH (Guruh a'zolarini faollashtirish uchun)
            if test_counter % 3 == 0 and test_counter < 30:
                time.sleep(1)
                reklama_matni = "📢 **Do'stlaringizni ham guruhga taklif qiling va bilimdonlar turnirida g'olib bo'ling!**"
                bot.send_message(GROUP_CHAT_ID, reklama_matni, parse_mode="Markdown")
            
            # 30 TA TEST TUGAGANDA REYTINGNI CHIQARISH
            if test_counter >= 30:
                time.sleep(20) 
                
                reyting_matni = "🔔 **30 ta test yakunlandi!**\n\n" + get_leaderboard_text()
                bot.send_message(GROUP_CHAT_ID, reyting_matni, parse_mode="Markdown")
                bot.send_message(GROUP_CHAT_ID, "⏳ **Navbatdagi turnir 15 daqiqadan so'ng boshlanadi. Ungacha guruhda faol bo'ling!**")
                
                poll_database.clear()
                test_counter = 0
                time.sleep(900)  # 15 daqiqa kutish
                
                bot.send_message(GROUP_CHAT_ID, "🚀 **Yangi turnir boshlandi! Ilk testlar yo'lda...**")
                continue
                
            time.sleep(300)  # Har 5 daqiqada yangi test
            
        except Exception as e:
            print(f"Test yuborishda xatolik: {e}")
            time.sleep(15)

if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=f"{RENDER_URL}/{API_TOKEN}", allowed_updates=['message', 'poll_answer'])
    print("Telegram Webhook faqat guruh uchun qaytadan sozlindi!")
    
    threading.Thread(target=test_sending_loop, daemon=True).start()
    
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
