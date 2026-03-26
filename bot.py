import telebot
import requests
import json
import os
from urllib.parse import quote

# Cấu hình - Lấy từ environment variable
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_BASE_URL = os.environ.get("API_BASE_URL")
ADMIN_KEY = os.environ.get("ADMIN_KEY", "admin2323")

BANK_CODE = os.environ.get("BANK_CODE", "vpb")
ACCOUNT_NUMBER = os.environ.get("ACCOUNT_NUMBER")
ACCOUNT_NAME = os.environ.get("ACCOUNT_NAME")
BANK_NAME = os.environ.get("BANK_NAME", "VP BANK")

AUTH_FILE = "authorized_users.json"

def load_authorized_users():
    if os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_authorized_users(users):
    with open(AUTH_FILE, 'w') as f:
        json.dump(list(users), f)

def is_authorized(user_id):
    return str(user_id) in load_authorized_users()

def authorize_user(user_id):
    users = load_authorized_users()
    users.add(str(user_id))
    save_authorized_users(users)

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if is_authorized(user_id):
        bot.reply_to(message, f"🏦 Bot đã sẵn sàng\n👤 {ACCOUNT_NAME}\n💰 {ACCOUNT_NUMBER}\n🏦 {BANK_NAME}\n\nGửi: [số tiền] [nội dung]\nVD: 500000 THANH TOAN")
    else:
        bot.reply_to(message, "🔐 Bot cần kích hoạt\n/key [mã_key]")

@bot.message_handler(commands=['key'])
def handle_key(message):
    user_id = message.from_user.id
    parts = message.text.split()
    if len(parts) == 2 and parts[1] == ADMIN_KEY:
        if not is_authorized(user_id):
            authorize_user(user_id)
            bot.reply_to(message, "✅ Kích hoạt thành công!\nGửi: [số tiền] [nội dung] để tạo QR")
        else:
            bot.reply_to(message, "🔓 Đã kích hoạt trước đó")
    else:
        bot.reply_to(message, "❌ Key không hợp lệ")

@bot.message_handler(func=lambda message: True)
def generate_qr(message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        bot.reply_to(message, "🔐 Chưa kích hoạt\n/key [mã_key]")
        return
    
    try:
        text = message.text.strip()
        parts = text.split(maxsplit=1)
        amount = parts[0].replace(",", "")
        note = parts[1] if len(parts) > 1 else ""
        
        amount_int = int(amount)
        if amount_int <= 0:
            bot.reply_to(message, "❌ Số tiền phải > 0")
            return
        
        if note:
            url = f"{API_BASE_URL}/{BANK_CODE}/{ACCOUNT_NUMBER}/{amount_int}/{quote(note)}"
        else:
            url = f"{API_BASE_URL}/{BANK_CODE}/{ACCOUNT_NUMBER}/{amount_int}"
        url += f"?frame=1&is_mask=0&accountName={quote(ACCOUNT_NAME)}"
        
        caption = f"🏦 {BANK_NAME}\n👤 {ACCOUNT_NAME}\n💰 {ACCOUNT_NUMBER}\n💵 {amount_int:,} VNĐ"
        if note:
            caption += f"\n📝 {note}"
        
        bot.send_photo(message.chat.id, url, caption=caption)
        
    except ValueError:
        bot.reply_to(message, "❌ Sai định dạng\nVD: 500000 THANH TOAN")
    except Exception as e:
        bot.reply_to(message, f"❌ Lỗi: {str(e)}")

if __name__ == "__main__":
    print("🤖 Bot polling đã chạy...")
    bot.infinity_polling(skip_pending=True)
