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

# REYTING JADVALINI TAYYORLASH
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

# 2. WEBHOOK ORQALI KELAYOTGAN BARCHA SO'ROVLAR
@app.route(f"/{API_TOKEN}", methods=['POST'])
def get_message():
    try:
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            
            # AGAR SINOVDAN O'TISH NATIJASI KELSA (Kafolatlangan yangi usul)
            if update.poll:
                poll_id = update.poll.id
                if poll_id in poll_database:
                    correct_id = poll_database[poll_id]
                    # To'g'ri javob variantidagi odamlar sonini tekshirish
                    options = update.poll.options
                    voters_count = options[correct_id].voter_count
                    print(f"[POLL) Test {poll_id} yangilandi. To'g'ri topganlar soni: {voters_count}")
            
            bot.process_new_updates([update])
            return "!", 200
    except Exception as e:
        print(f"Webhook xatosi: {e}")
    return "!", 200

@app.route("/", methods=['GET'])
def index():
    return "Bot muvaffaqiyatli ishlamoqda!", 200

# 3. KAFOLATLANGAN FOYDALANUVCHILARNI RO'YXATGA OLISH (TUZATILDI)
@bot.poll_answer_handler()
def handle_poll_answer(poll_answer):
    global user_scores
    try:
        poll_id = poll_answer.poll_id
        user_id = poll_answer.user.id
        
        first_name = poll_answer.user.first_name if poll_answer.user.first_name else "Bilimdon"
        last_name = poll_answer.user.last_name if poll_answer.user.last_name else ""
        full_name = f"{first_name} {last_name}".strip()
        
        if poll_id in poll_database:
            correct_id = poll_database[poll_id]
            user_answers = poll_answer.option_ids
            
            if user_answers and user_answers[0] == correct_id:
                if user_id not in user_scores:
                    user_scores[user_id] = {"name": full_name, "score": 0}
                user_scores[user_id]["score"] += 1
                print(f"✅ [BALL QO'SHILDI] {full_name} — {user_scores[user_id]['score']} ball")
    except Exception as e:
        print(f"Ovoz hisoblashda xato: {e}")

# 4. /REYTING BUYRUG'I
@bot.message_handler(commands=['reyting'])
def send_leaderboard(message):
    try:
        text = get_leaderboard_text()
        bot.reply_to(message, text, parse_mode="Markdown")
    except Exception as e:
        print(f"Reyting jo'natishda xato: {e}")

# 5. ASOSIY TEST TASHLOVCHI TSIKL
def test_sending_loop():
    global test_counter, poll_database
    time.sleep(5)  
    print("Testlar yuborilishi boshlandi...")
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
            
            # GURUHGA TEST TASHLOVCHI (Ochiq ovoz berish)
            group_poll = bot.send_poll(
                chat_id=GROUP_CHAT_ID,
                question=f"🇬🇧 {word} — so'zining tarjimasini toping:",
                options=options,
                type='quiz',
                correct_option_id=correct_index,
                is_anonymous=False  # Odamlar ismi ko'rinishi shart!
            )
            poll_database[group_poll.poll.id] = correct_index
            
            test_counter += 1
            print(f"Test #{test_counter} guruhga yuborildi.")
            
            # 30 TA TEST TUGAGANDA REYTINGNI CHIQARISH
            if test_counter >= 30:
                time.sleep(15) 
                
                reyting_matni = "🔔 **30 ta test yakunlandi!**\n\n" + get_leaderboard_text()
                bot.send_message(GROUP_CHAT_ID, reyting_matni, parse_mode="Markdown")
                bot.send_message(GROUP_CHAT_ID, "⏳ **Navbatdagi turnir 15 daqiqadan so'ng boshlanadi.**")
                
                poll_database.clear()
                test_counter = 0
                time.sleep(900)  # 15 daqiqa kutish
                
                bot.send_message(GROUP_CHAT_ID, "🚀 **Yangi turnir boshlandi! Ilk testlar yo'lda...**")
                continue
                
            time.sleep(60)  # Har 5 daqiqada bitta test
            
        except Exception as e:
            print(f"Test yuborishda xatolik: {e}")
            time.sleep(15)

if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(1)
    # Webhook ulanishini sozlash (barcha yangilanishlar bilan)
    bot.set_webhook(
        url=f"{RENDER_URL}/{API_TOKEN}", 
        allowed_updates=['message', 'poll', 'poll_answer']
    )
    print("Yangi mukammal Webhook o'rnatildi!")
    
    threading.Thread(target=test_sending_loop, daemon=True).start()
    
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
