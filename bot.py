import telebot
import pandas as pd
from datetime import datetime
import os
import math

TOKEN = "7780206034:AAHQgPpk2z5jxqU-4KGGA0VcA16lZo94qkU"

bot = telebot.TeleBot(TOKEN)

FILE_NAME = "davomat.xlsx"

# =========================
# GPS
# =========================
OFFICE_LAT = 42.308964
OFFICE_LON = 69.726254

MAX_DISTANCE = 100

# =========================
# EXCEL
# =========================
if not os.path.exists(FILE_NAME):

    df = pd.DataFrame(columns=[
        "Ism",
        "Sana",
        "Keldi",
        "Ketdi",
        "Ish_soati",
        "Holat"
    ])

    df.to_excel(FILE_NAME, index=False)

# =========================
# DISTANCE
# =========================
def distance(lat1, lon1, lat2, lon2):

    R = 6371000

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(dlambda / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return R * c

# =========================
# START
# =========================
@bot.message_handler(commands=['start'])
def start(message):

    markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keldim_btn = telebot.types.KeyboardButton(
        "📍 Keldim",
        request_location=True
    )

    ketdim_btn = telebot.types.KeyboardButton(
        "Ketdim"
    )

    markup.add(keldim_btn)
    markup.add(ketdim_btn)

    bot.send_message(
        message.chat.id,
        "✅ Davomat botiga xush kelibsiz",
        reply_markup=markup
    )

# =========================
# KELDIM
# =========================
@bot.message_handler(content_types=['location'])
def location(message):

    user_lat = message.location.latitude
    user_lon = message.location.longitude

    masofa = distance(
        OFFICE_LAT,
        OFFICE_LON,
        user_lat,
        user_lon
    )

    if masofa > MAX_DISTANCE:

        bot.send_message(
            message.chat.id,
            "❌ Siz ishxona hududida emassiz"
        )

        return

    now = datetime.now()

    holat = "OK"

    if now.hour > 8 or (
        now.hour == 8
        and now.minute > 10
    ):

        holat = "Kech qoldi"

    df = pd.read_excel(FILE_NAME, dtype=str)

    new_row = {
        "Ism": message.from_user.first_name,
        "Sana": now.strftime("%Y-%m-%d"),
        "Keldi": now.strftime("%H:%M:%S"),
        "Ketdi": "",
        "Ish_soati": "",
        "Holat": holat
    }

    df = pd.concat(
        [df, pd.DataFrame([new_row])],
        ignore_index=True
    )

    df.to_excel(FILE_NAME, index=False)

    bot.send_message(
        message.chat.id,
        f"✅ Davomat qabul qilindi\nHolat: {holat}"
    )

# =========================
# KETDIM
# =========================
@bot.message_handler(func=lambda m: m.text == "Ketdim")
def ketdim(message):

    now = datetime.now()

    df = pd.read_excel(FILE_NAME, dtype=str)

    ism = message.from_user.first_name

    topildi = False

    for i in range(len(df)-1, -1, -1):

        if (
            df.loc[i, 'Ism'] == ism
            and (
                pd.isna(df.loc[i, 'Ketdi'])
                or df.loc[i, 'Ketdi'] == ""
            )
        ):

            kelgan = datetime.strptime(
                df.loc[i, 'Keldi'],
                "%H:%M:%S"
            )

            ketgan = datetime.strptime(
                now.strftime("%H:%M:%S"),
                "%H:%M:%S"
            )

            ish_soati = round(
                (ketgan - kelgan).seconds / 3600,
                2
            )

            df.loc[i, 'Ketdi'] = now.strftime("%H:%M:%S")
            df.loc[i, 'Ish_soati'] = str(ish_soati)

            if now.hour < 18:
                df.loc[i, 'Holat'] += " | Erta ketdi"

            df.to_excel(FILE_NAME, index=False)

            bot.send_message(
                message.chat.id,
                f"✅ Ketgan vaqt saqlandi\nIsh soati: {ish_soati}"
            )

            topildi = True
            break

    if not topildi:

        bot.send_message(
            message.chat.id,
            "❌ Avval Keldim bosing"
        )

# =========================
# OYLIK
# =========================
@bot.message_handler(commands=['oylik'])
def oylik(message):

    df = pd.read_excel(FILE_NAME, dtype=str)

    result = "📊 Oylik hisob\n\n"

    for ism in df['Ism'].unique():

        ish_kuni = len(
            df[df['Ism'] == ism]
        )

        oylik_sum = round(
            (200000 / 30) * ish_kuni
        )

        result += (
            f"👤 {ism}\n"
            f"📅 Ish kuni: {ish_kuni}\n"
            f"💰 Oylik: {oylik_sum} tg\n\n"
        )

    bot.send_message(
        message.chat.id,
        result
    )

# =========================
# EXCEL YUBORISH
# =========================
@bot.message_handler(commands=['excel'])
def excel(message):

    with open(FILE_NAME, 'rb') as file:

        bot.send_document(
            message.chat.id,
            file
        )

print("Bot ishga tushdi ✅")

bot.infinity_polling()
