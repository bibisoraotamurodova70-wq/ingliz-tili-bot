from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import telebot
import time
import requests
import random
import os
from deep_translator import GoogleTranslator

# 1. RENDER UCHUN MUKAMMAL VEB SERVER QISMI
class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("Bot ishlamoqda!", "utf-8"))

def run_web_server():
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), MyServer)
    print(f"Veb-server {port}-portda muvaffaqiyatli ishga tushdi.")
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# 2. BOT PARAMETRLARI
API_TOKEN = '8972113004:AAHhJnR6bODO7-CpYqAnFXwrtiiyWR2x7Io'
GROUP_CHAT_ID = '@testlar_bazasi_ingiliz'   # Guruh manzili
CHANNEL_CHAT_ID = '@ingiliz_turnir'         # Kanal manzili

bot = telebot.TeleBot(API_TOKEN)
translator = GoogleTranslator(source='en', target='uz')

user_scores = {}
poll_database = {}
test_counter = 0  # Tashlangan testlarni sanash uchun o'zgaruvchi

# Chalg'ituvchi variantlar uchun 200 ta o'zbekcha so'zlar bazasi
fake_answers = [
    "olma", "kitob", "uy", "mashina", "yugurmoq", "baxtli", "sovuq", "issiq", 
    "yozmoq", "suv", "non", "shahar", "yaxshi", "yomon", "katta", "kichik",
    "stul", "stol", "deraza", "eshik", "maktab", "o'qituvchi", "o'quvchi", "ruchka",
    "daftar", "telefon", "kompyuter", "soat", "kalit", "sumka", "pul", "hamyon",
    "nonushta", "tushlik", "kechki ovqat", "sut", "choy", "kofe", "shakar", "tuz",
    "go'sht", "baliq", "guruch", "sabzi", "kartoshka", "piyoz", "meva", "sabzavot",
    "sariyog'", "pishloq", "tuxum", "asal", "sharbat", "muzqaymoq",
    "daraxt", "gul", "o't", "barg", "osmon", "quyosh", "oy", "yulduz",
    "bulut", "yomg'ir", "qor", "shamol", "havo", "yer", "tosh", "qum",
    "daryo", "ko'l", "deniz", "okean", "tog'", "vodiydan", "o'rmon", "bog'",
    "ota", "ona", "aka", "uka", "opa", "singil", "do'st", "bola",
    "odam", "erkak", "ayol", "qo'shni", "shifokor", "haydovchi", "muhandis", "asbob",
    "ko'cha", "bino", "do'kon", "bozor", "shifoxona", "dorixona", "mehmonxona", "bekat",
    "aeroport", "vokzal", "zavod", "idora", "teatr", "muzey", "park", "guruh",
    "it", "mushuk", "ot", "sigir", "qo'y", "tovuq", "qush",
    "sher", "ayiq", "bo'ri", "tulki", "quyon", "sichqon", "fil", "maymun",
    "kiyim", "ko'ylak", "shim", "poyabzal", "shlyapa", "qo'lqop", "ko'zoynak", "uzuk",
    "bosh", "ko'z", "quloq", "burun", "og'iz", "tish", "qo'l", "oyoq",
    "yurak", "soch", "yuz", "bo'yin", "yona", "orqa", "qorin", "tana",
    "yurmoq", "kelmoq", "ketmoq", "o'tirmoq", "turmoq", "uxlamoq", "uyg'onmoq", "kulmoq",
    "yig'lamoq", "gapirmoq", "tinglamoq", "ko'rmoq", "eshitmoq", "o'ylamoq", "bilmoq", "tushunmoq",
    "ochmoq", "yopmoq", "olmoq", "bermoq", "sotmoq", "sotib olmoq", "tuzatmoq", "sindirmoq",
    "chizmoq", "bo'yamoq", "yuvmoq", "tozalamoq", "pishirmoq", "yemoq", "ichmoq", "sakramoq",
    "go'zal", "xunuk", "aqlli", "ahmoq", "kuchli", "kuchsiz", "boy", "kambag'al",
    "yosh", "eski", "yangi", "chaqqon", "sekin", "tez", "og'ir", "yengil",
    "toza", "kir", "shirin", "achchiq", "nordon", "sho'r", "arzon", "qimmat",
    "oson", "qiyin", "to'g'ri", "noto'g'ri", "uzun", "kalta", "keng", "tor"
]

def get_random_word():
    try:
        response = requests.get("https://random-word-api.herokuapp.com/word?number=1")
        if response.status_code == 200:
            return response.json()[0].capitalize()
    except:
        return None

# 3. GURUHDA JAVOB BERGANLARNI TEKSHIRISH
@bot.poll_answer_handler()
def handle_poll_answer(poll_answer):
    poll_id = poll_answer.poll_id
    user_id = poll_answer.user.id
    
    first_name = poll_answer.user.first_name
    last_name = poll_answer.user.last_name if poll_answer.user.last_name else ""
    full_name = f"{first_name} {last_name}".strip()
    
    if poll_id in poll_database:
        correct_id = poll_database[poll_id]
        user_answers = poll_answer.option_ids
        
        if user_answers and user_answers[0] == correct_id:
            if user_id not in user_scores:
                user_scores[user_id] = {"name": full_name, "score": 0}
            user_scores[user_id]["score"] += 1

# REYTINGNI MATN SHAKLIDA TAYYORLASH FUNKSIYASI
def get_leaderboard_text():
    if not user_scores:
        return "📊 Hozircha guruhda hech kim ball to'plamadi."
        
    sorted_users = sorted(user_scores.values(), key=lambda x: x['score'], reverse=True)
    leaderboard_text = "📊 **Guruhdagi eng bilimdonlar reytingi (Top 10):**\n\n"
    medals = {1: "🥇 1-o'rin", 2: "🥈 2-o'rin", 3: "🥉 3-o'rin"}
    
    for index, user in enumerate(sorted_users[:10], start=1):
        place_text = medals.get(index, f"🔹 {index}-o'rin")
        leaderboard_text += f"{place_text}: {user['name']} — {user['score']} ball\n"
    return leaderboard_text

# 4. /REYTING BUYRUG'I (Qo'lda tekshirish uchun ham qoldi)
@bot.message_handler(commands=['reyting'])
def send_leaderboard(message):
    text = get_leaderboard_text()
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

def start_polling():
    bot.infinity_polling(skip_pending=True)

threading.Thread(target=start_polling, daemon=True).start()

print("Bot guruh va kanal uchun reyting va tanaffus tizimi bilan ishga tushdi...")

# 5. ASOSIY ISH TSIKLI
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
        
        # GURUHGA YUBORISH
        group_poll = bot.send_poll(
            chat_id=GROUP_CHAT_ID,
            question=word,
            options=options,
            type='quiz',
            correct_option_id=correct_index,
            is_anonymous=False
        )
        poll_database[group_poll.poll.id] = correct_index
        
        # KANALGA YUBORISH
        bot.send_poll(
            chat_id=CHANNEL_CHAT_ID,
            question=word,
            options=options,
            type='quiz',
            correct_option_id=correct_index
        )
        
        test_counter += 1  # Testni bittaga oshiramiz
        print(f"Test #{test_counter} yuklandi: {word} -> {correct_uz}")
        
        # AGAR 30 TA TEST BO'LGAN BO'LSA
        if test_counter >= 30:
            time.sleep(10) # Oxirgi testni yechib olishlari uchun 10 soniya kutamiz
            
            # 1. Avtomatik reyting jadvalini guruhga tashlaymiz
            reyting_matni = "🔔 **30 ta test yakunlandi!**\n\n" + get_leaderboard_text()
            bot.send_message(GROUP_CHAT_ID, reyting_matni, parse_mode="Markdown")
            
            # 2. Tanaffus haqida xabar beramiz
            bot.send_message(GROUP_CHAT_ID, "⏳ **Navbatdagi turnir 15 daqiqadan so'ng boshlanadi. Biroz dam oling!**")
            
            # Sanoqni qayta nollaymiz
            test_counter = 0
            
            # 15 daqiqa (900 soniya) tanaffus qilib uxlaydi
            time.sleep(900)
            
            bot.send_message(GROUP_CHAT_ID, "🚀 **Yangi turnir boshlandi! Ilk testlar yo'lda...**")
            continue # Tsikl boshiga qaytadi
            
        # Asosiy kutish vaqti: 5 daqiqa (300 soniya)
        time.sleep(300)
        
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
        time.sleep(15)
