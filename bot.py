import os
import time
import telebot
import pandas as pd
import cloudscraper
from io import BytesIO

TOKEN = os.environ.get("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Tạo scraper (giúp bypass Cloudflare/Zalo tốt hơn)
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

def check_has_zalo(phone):
    if not phone or str(phone).strip() == "":
        return False
    
    # Làm sạch số điện thoại
    phone_str = str(phone).strip().replace("+84", "0").replace(" ", "").replace("-", "").replace(".", "")
    if phone_str.startswith("84"):
        phone_str = "0" + phone_str[2:]
    if not phone_str.startswith("0"):
        phone_str = "0" + phone_str
    
    url = f"https://zalo.me/{phone_str}"
    
    try:
        r = scraper.get(url, timeout=12)
        
        text = r.text.lower()
        current_url = r.url.lower()
        
        # Không thể check (yêu cầu đăng nhập)
        if "đăng nhập" in text or "login" in text or "id.zalo.me/account/login" in current_url:
            return "cannot_check"
        
        # Không có Zalo
        if "tài khoản này không tồn tại hoặc không cho phép tìm kiếm" in text:
            return False
        
        # Có Zalo
        return True
    except:
        return False

@bot.message_handler(content_types=['document'])
def handle_document(message):
    doc = message.document
    if not doc.file_name.lower().endswith(('.xlsx', '.xls', '.xlsm')):
        bot.reply_to(message, "❌ Chỉ hỗ trợ file Excel (.xlsx, .xls, .xlsm)")
        return
    
    bot.reply_to(message, f"🔄 Đang xử lý file `{doc.file_name}`...\nFile lớn có thể mất vài phút.")
    
    try:
        file_info = bot.get_file(doc.file_id)
        file_content = bot.download_file(file_info.file_path)
        excel_io = BytesIO(file_content)
        
        df = pd.read_excel(excel_io, engine='openpyxl', header=0)
        
        if len(df.columns) < 3:
            bot.reply_to(message, "❌ File phải có ít nhất cột C chứa số điện thoại")
            return
        
        keep_indices = [0]  # giữ header
        cannot_check = False
        total = len(df) - 1
        
        for i in range(1, len(df)):
            if (i % 50 == 0):
                bot.send_message(message.chat.id, f"⏳ Đã check {i}/{total} số...")
            
            phone = df.iloc[i, 2]  # cột C
            result = check_has_zalo(phone)
            
            if result == "cannot_check":
                cannot_check = True
                break
            if result:  # có Zalo
                keep_indices.append(i)
        
        if cannot_check:
            bot.reply_to(message, "không thể check file")
            return
        
        # Tạo file kết quả
        filtered_df = df.iloc[keep_indices]
        output = BytesIO()
        filtered_df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        
        new_name = "S" + doc.file_name
        
        bot.send_document(
            message.chat.id,
            document=output,
            filename=new_name,
            caption=f"✅ Đã lọc xong!\nTổng số đã check: {total}\nSố có Zalo: {len(keep_indices)-1}\nFile mới: {new_name}"
        )
        
    except Exception as e:
        bot.reply_to(message, f"❌ Lỗi xử lý: {str(e)}")

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 Bot lọc Zalo (không Selenium) sẵn sàng!\nGửi file Excel cho mình nhé.\n- Hàng đầu tiên là header (bỏ qua)\n- Số điện thoại phải ở **cột C**")

print("🚀 Bot lọc Zalo (requests + cloudscraper) đang chạy...")
bot.infinity_polling()
