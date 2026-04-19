import os
import time
import telebot
import pandas as pd
from io import BytesIO
import undetected_chromedriver as uc

TOKEN = os.environ.get("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Khởi tạo undetected Chrome (bypass tốt hơn)
options = uc.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-gpu")

driver = uc.Chrome(options=options, use_subprocess=True)

def check_number(phone):
    if not phone or str(phone).strip() == "":
        return False
    
    phone_str = str(phone).strip().replace("+84", "0").replace(" ", "").replace("-", "").replace(".", "")
    if phone_str.startswith("84"):
        phone_str = "0" + phone_str[2:]
    if not phone_str.startswith("0"):
        phone_str = "0" + phone_str
    
    url = f"https://zalo.me/{phone_str}"
    
    try:
        driver.get(url)
        time.sleep(5)  # chờ load trang
        
        page_text = driver.page_source.lower()
        current_url = driver.current_url.lower()
        
        if "đăng nhập" in page_text or "login" in page_text or "id.zalo.me/account/login" in current_url:
            return "cannot_check"
        
        if "tài khoản này không tồn tại hoặc không cho phép tìm kiếm" in page_text:
            return False
        
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
        
        keep_indices = [0]
        cannot_check = False
        total = len(df) - 1
        
        for i in range(1, len(df)):
            if (i % 30 == 0):
                bot.send_message(message.chat.id, f"⏳ Đã kiểm tra {i}/{total} dòng...")
            
            phone = df.iloc[i, 2]
            result = check_number(phone)
            
            if result == "cannot_check":
                cannot_check = True
                break
            if result:
                keep_indices.append(i)
        
        if cannot_check:
            bot.reply_to(message, "không thể kiểm tra file")
            return
        
        filtered_df = df.iloc[keep_indices]
        output = BytesIO()
        filtered_df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        
        new_name = "S" + doc.file_name
        
        bot.send_document(
            message.chat.id,
            document=output,
            filename=new_name,
            caption=f"✅ Hoàn tất!\nTổng số đã kiểm tra: {total}\nSố giữ lại: {len(keep_indices)-1}"
        )
        
    except Exception as e:
        bot.reply_to(message, f"❌ Lỗi xử lý: {str(e)}")

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 Bot sẵn sàng!\nGửi file Excel cho mình.\n- Hàng đầu tiên là header (bỏ qua)\n- Số điện thoại phải nằm ở **cột C**")

print("Bot đang chạy...")
bot.infinity_polling()
