import os, requests, logging
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters

logging.basicConfig(level=logging.INFO)
TOKEN = "8691344282:AAGM2VykrOhl48bpH48qgZ2Y1y4_QwNDUxw"
DOWNLOAD_DIR = "/app/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
user_urls = {}

def start(update, context):
    update.message.reply_text("مرحبا! ارسل رابط فيديو")

def download_tiktok(url):
    try:
        r = requests.get(f"https://tikwm.com/api/?url={url}&hd=1", timeout=15).json()
        if r.get("code") == 0:
            video_url = r["data"].get("hdplay") or r["data"].get("play")
            path = f"{DOWNLOAD_DIR}/tiktok.mp4"
            with open(path, "wb") as f:
                f.write(requests.get(video_url, timeout=30).content)
            return path, r["data"].get("title","tiktok")
    except:
        pass
    return None, None

def handle_url(update, context):
    url = update.message.text.strip()
    if not url.startswith("http"):
        update.message.reply_text("ارسل رابط صحيح")
        return
    user_urls[update.effective_user.id] = url
    if "tiktok.com" in url:
        msg = update.message.reply_text("كنحمل...")
        path, title = download_tiktok(url)
        if path:
            with open(path, "rb") as f:
                update.message.reply_video(video=f, caption=title)
            os.remove(path)
            msg.delete()
        else:
            msg.edit_text("فشل")
        return
    keyboard = [[InlineKeyboardButton("720p", callback_data="video_720"), InlineKeyboardButton("MP3", callback_data="audio_mp3")]]
    update.message.reply_text("شنو تبغي؟", reply_markup=InlineKeyboardMarkup(keyboard))

def handle_choice(update, context):
    query = update.callback_query
    query.answer()
    url = user_urls.get(query.from_user.id)
    if not url:
        query.edit_message_text("ارسل الرابط")
        return
    query.edit_message_text("كنحمل...")
    choice = query.data
    if choice == "audio_mp3":
        ydl_opts = {"format": "bestaudio/best", "outtmpl": f"{DOWNLOAD_DIR}/%(id)s.%(ext)s", "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}], "quiet": True}
    else:
        ydl_opts = {"format": "best[height<=720][filesize<50M]/best", "outtmpl": f"{DOWNLOAD_DIR}/%(id)s.%(ext)s", "quiet": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            fp = ydl.prepare_filename(info)
            if choice == "audio_mp3":
                fp = os.path.splitext(fp)[0] + ".mp3"
        with open(fp, "rb") as f:
            if choice == "audio_mp3":
                query.message.reply_audio(audio=f, title=info.get("title","audio"))
            else:
                query.message.reply_video(video=f, caption=info.get("title","video"))
        os.remove(fp)
        query.delete_message()
    except Exception as e:
        query.edit_message_text(f"خطا: {str(e)[:200]}")

updater = Updater(TOKEN)
dp = updater.dispatcher
dp.add_handler(CommandHandler("start", start))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_url))
dp.add_handler(CallbackQueryHandler(handle_choice))
print("البوت شغال")
updater.start_polling()
updater.idle()
