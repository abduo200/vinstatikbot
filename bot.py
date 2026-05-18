import os, requests
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8691344282:AAGM2VykrOhl48bpH48qgZ2Y1y4_QwNDUxw"
DOWNLOAD_DIR = os.path.expanduser("~/downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
user_urls = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحبا! ارسل رابط فيديو")

def download_tiktok(url):
    try:
        api = f"https://tikwm.com/api/?url={url}&hd=1"
        r = requests.get(api, timeout=15).json()
        if r.get("code") == 0:
            video_url = r["data"].get("hdplay") or r["data"].get("play")
            title = r["data"].get("title", "tiktok")
            path = f"{DOWNLOAD_DIR}/tiktok.mp4"
            with open(path, "wb") as f:
                f.write(requests.get(video_url, timeout=30).content)
            return path, title
    except:
        pass
    return None, None

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith("http"):
        await update.message.reply_text("ارسل رابط صحيح")
        return
    user_urls[update.effective_user.id] = url
    if "tiktok.com" in url:
        msg = await update.message.reply_text("كنحمل...")
        path, title = download_tiktok(url)
        if path:
            with open(path, "rb") as f:
                await update.message.reply_video(video=f, caption=title, supports_streaming=True)
            os.remove(path)
            await msg.delete()
        else:
            await msg.edit_text("فشل التحميل")
        return
    keyboard = [[InlineKeyboardButton("720p", callback_data="video_720"), InlineKeyboardButton("MP3", callback_data="audio_mp3")]]
    await update.message.reply_text("شنو تبغي؟", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    url = user_urls.get(query.from_user.id)
    if not url:
        await query.edit_message_text("ارسل الرابط من جديد")
        return
    choice = query.data
    await query.edit_message_text("كنحمل...")
    if choice == "audio_mp3":
        ydl_opts = {"format": "bestaudio/best", "outtmpl": f"{DOWNLOAD_DIR}/%(id)s.%(ext)s", "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}], "quiet": True}
    else:
        ydl_opts = {"format": "best[height<=720][filesize<50M]/best[filesize<50M]/best", "outtmpl": f"{DOWNLOAD_DIR}/%(id)s.%(ext)s", "quiet": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if choice == "audio_mp3":
                file_path = os.path.splitext(file_path)[0] + ".mp3"
        with open(file_path, "rb") as f:
            if choice == "audio_mp3":
                await query.message.reply_audio(audio=f, title=info.get("title","audio"))
            else:
                await query.message.reply_video(video=f, caption=info.get("title","video"), supports_streaming=True)
        os.remove(file_path)
        await query.delete_message()
    except Exception as e:
        await query.edit_message_text(f"خطا: {str(e)[:200]}")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
app.add_handler(CallbackQueryHandler(handle_choice))
print("البوت شغال")
app.run_polling()
