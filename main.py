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
    # Render o'zi bergan portni oladi (masalan, 10000), agar topilmasa 8000 ni oladi
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), MyServer)
    print(f"Veb-server {port}-portda muvaffaqiyatli ishga tushdi.")
    server.serve_forever()

# Veb serverni alohida fonda (thread) shartta ishga tushiramiz
threading.Thread(target=run_web_server, daemon=True).start()

# 2. BOT PARAMETRLARI
API_TOKEN = '8972113004:AAHhJnR6bODO7-CpYqAnFXwrtiiyWR2x7Io'
CHAT_ID = '@testlar_bazasi_ingiliz'

bot = telebot.TeleBot(API_TOKEN)
translator = GoogleTranslator(source='en', target='uz')

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
    """Internetdan tasodifiy inglizcha so'z oladi"""
    try:
        response = requests.get("https://random-word-api.herokuapp.com/word?number=1")
        if response.status_code == 200:
            return response.json()[0].capitalize()
    except:
        return None

print("Cheksiz avtomat bot ishga tushdi...")

# 3. CHEKSIZ TSIKL (BOTNING ASOSIY ISHI)
while True:
    try:
        word = get_random_word()
        if not word:
            time.sleep(10)
            continue
            
        # So'zni o'zbekchaga o'girish
        correct_uz = translator.translate(word).lower()
        
        # Agar tarjimasi topilmasa yoki inglizcha so'z o'zgarmay qolsa o'tkazib yuboramiz
        if word.lower() == correct_uz:
            continue
            
        # 3 ta noto'g'ri variant tanlash
        wrong_options = random.sample(fake_answers, 3)
        
        if correct_uz in wrong_options:
            continue
            
        # Variantlarni birlashtirish va aralashtirish
        options = wrong_options + [correct_uz]
        random.shuffle(options)
        
        correct_index = options.index(correct_uz)
        
        # Telegramga Quiz yuborish
        bot.send_poll(
            chat_id=CHAT_ID,
            question=word,
            options=options,
            type='quiz',
            correct_option_id=correct_index,
            is_anonymous=True
        )
        print(f"Muvaffaqiyatli yuklandi: {word} -> {correct_uz}")
        
        # Har 1 daqiqada (60 soniya) bitta test tashlaydi
        time.sleep(120)
        
    except Exception as e:
        print(f"Xatolik yuz berdi, 15 soniya kutiladi: {e}")
        time.sleep(15)
