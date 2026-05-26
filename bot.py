import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import math

TOKEN = "7780206034:AAHQgPpk2z5jxqU-4KGGA0VcA16lZo94qkU"

bot = telebot.TeleBot(TOKEN)

# =========================
# GOOGLE SHEETS
# =========================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "braided-pride-497505-t3-5bac59d67178.json",
    scope
)

client = gspread.authorize(creds)

sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1BgmUzqVfjVKRcSrv-qgIhIETNznWXlec7z31_Gio3vE/edit?usp=sharing"
).sheet1

# =========================
# GPS
# =========================
OFFICE_LAT = 42.308964
OFFICE_LON = 69.726254

MAX_DISTANCE = 100

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
        "Davomat botiga xush kelibsiz ✅",
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

    row = [
        message.from_user.first_name,
        now.strftime("%Y-%m-%d"),
        now.strftime("%H:%M:%S"),
        "",
        "",
        holat
    ]

    sheet.append_row(row)

    bot.send_message(
        message.chat.id,
        f"✅ Davomat qabul qilindi\nHolat: {holat}"
    )

# =========================
# KETDIM
# =========================
@bot.message_handler(func=lambda m: m.text == "Ketdim")
def ketdim(message):

    data = sheet.get_all_values()

    ism = message.from_user.first_name

    now = datetime.now()

    for i in range(len(data), 1, -1):

        row = data[i - 1]

        if row[0] == ism and row[3] == "":

            kelgan = datetime.strptime(
                row[2],
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

            sheet.update_cell(i, 4, now.strftime("%H:%M:%S"))
            sheet.update_cell(i, 5, str(ish_soati))

            holat = row[5]

            if now.hour < 18:
                holat += " | Erta ketdi"

            sheet.update_cell(i, 6, holat)

            bot.send_message(
                message.chat.id,
                f"✅ Ketgan vaqt saqlandi\nIsh soati: {ish_soati}"
            )

            return

    bot.send_message(
        message.chat.id,
        "❌ Avval Keldim bosing"
    )

# =========================
# OYLIK
# =========================
@bot.message_handler(commands=['oylik'])
def oylik(message):

    data = sheet.get_all_values()

    result = "📊 Oylik hisob\n\n"

    names = []

    for row in data[1:]:

        if row[0] not in names:
            names.append(row[0])

    for ism in names:

        ish_kuni = 0

        for row in data[1:]:

            if row[0] == ism:
                ish_kuni += 1

        oylik = round(
            (200000 / 30) * ish_kuni
        )

        result += (
            f"👤 {ism}\n"
            f"📅 Ish kuni: {ish_kuni}\n"
            f"💰 Oylik: {oylik} tg\n\n"
        )

    bot.send_message(
        message.chat.id,
        result
    )

print("Bot ishga tushdi ✅")

bot.infinity_polling()
