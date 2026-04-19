import os
import time
import telebot
import pandas as pd
from io import BytesIO

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

TOKEN = os.environ.get("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Khởi tạo Chrome (chạy 1 lần)
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

def check_has_zalo(phone):
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
        time.sleep(4)  # chờ load trang
        
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
    
    bot.reply_to(message, "🔄 Đang xử lý file bằng Selenium... Có thể mất thời gian nếu file lớn.")
    
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
        
        for i in range(1, len(df)):
            phone = df.iloc[i, 2]  # cột C
            result = check_has_zalo(phone)
            
            if result == "cannot_check":
                cannot_check = True
                break
            if result:
                keep_indices.append(i)
        
        if cannot_check:
            bot.reply_to(message, "không thể check file")
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
            caption="✅ Đã lọc xong bằng Selenium!\nSố có Zalo đã giữ lại và dồn lên."
        )
    except Exception as e:
        bot.reply_to(message, f"❌ Lỗi: {str(e)}")

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 Bot lọc Zalo (Selenium) sẵn sàng!\nGửi file Excel cho mình.\nSố điện thoại phải nằm ở **cột C**.")

print("Bot Selenium đang chạy...")
bot.infinity_polling()
