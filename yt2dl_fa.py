#MmD
import re
import os
import json
import time
import uuid
import string
import random
import string
import telebot
import subprocess
from telebot import types
import yt_dlp as youtube_dl
from youtube_dl.utils import sanitize_filename

API_TOKEN = 'API_TOKEN'
bot = telebot.TeleBot(API_TOKEN)
channel_id = "@Your_Channel"
directory = '/var/www/html'
base_url = 'http://IP_OR_DOMAIN/'
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

video_urls = {}
last_message_time = {}
video_formats_cache = {}
last_action_time = {}

now = time.time()
two_hours_ago = now - (2 * 60 * 60)  # 2 hours in seconds

for filename in os.listdir(directory):
    filepath = os.path.join(directory, filename)
    if os.path.isfile(filepath) and filename != 'index.html':
        modified_time = os.path.getmtime(filepath)
        if modified_time < two_hours_ago:
            os.remove(filepath)

def is_user_in_channel(user_id):
    try:
        member = bot.get_chat_member(channel_id, user_id)
        return member.status not in ("left", "kicked")
    except Exception as e:
        print(f"Error checking user membership: {e}")
        return False

def send_join_channel_message(chat_id):
    bot.send_message(chat_id, "برای استفاده از این ربات لطفا عضو این کانال شوید: " + channel_id)
        
def is_valid_youtube_url(url):
    youtube_regex = r'(https?://)?(www\.)?((youtube\.com/)|(youtu\.be/)|(m\.youtube\.com/)|(m\.youtu\.be/))'
    return re.match(youtube_regex, url) is not None
    
def sanitize_filename(filename, max_length=50):
    valid_chars = set(string.ascii_letters + string.digits + " -_.()")
    sanitized_name = ''.join(c for c in filename if c in valid_chars)
    return sanitized_name.strip()[:max_length]

def random_string(length):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for _ in range(length))
    
def get_youtube_formats(url):
    try:
        with youtube_dl.YoutubeDL({'quiet': True, 'no_warnings': True, 'ignoreerrors': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            if info is None:
                return []
            formats = info.get('formats')
            formats = [fmt for fmt in formats if fmt.get('vcodec') != 'none']
            formats = [fmt for fmt in formats if fmt.get('acodec') is not None]
            return formats
    except youtube_dl.utils.DownloadError:
        return []


def separate_formats_with_without_audio(formats):
    with_audio = []
    without_audio = []
    for format in formats:
        if has_audio(format):
            with_audio.append(format)
        else:
            without_audio.append(format)

    return with_audio, without_audio

def download_and_send_video(chat_id, url, format_id):
    bot.send_message(chat_id, "درحال ارسال فایل، لطفا صبر کنید ⏳")
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'format': format_id,
        'outtmpl': 'video.%(ext)s',
        'noplaylist': True
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_name = f'video.{info["ext"]}'
        file_size = os.path.getsize(video_name)
        if file_size > MAX_FILE_SIZE:
            video_title = info.get('title', None)
            sanitized_title = sanitize_filename(video_title)
            new_name = f'{sanitized_title}_{str(uuid.uuid4())}.{info["ext"]}'
            new_name = new_name.replace(' ', '+') # replace space with '+'
            os.rename(video_name, os.path.join('/var/www/html', new_name))
            video_url = f'{base_url}{new_name}'
            caption = f"{sanitized_title}\n{channel_id}"
            bot.send_message(chat_id, f"حجم ویدیو درخواستی بالاتر از 50 مگابایت است، لطفا از طریق این لینک دانلود کنید: {video_url}")
        else:
            video_title = info.get('title', None)
            sanitized_title = sanitize_filename(video_title)
            caption = f"{sanitized_title}\n{channel_id}"
            with open(video_name, 'rb') as video_file:
                bot.send_video(chat_id, video_file, caption=caption)
            os.remove(video_name)

def download_and_send_audio(chat_id, url):
    bot.send_message(chat_id, "درحال ارسال فایل، لطفا صبر کنید ⏳")
    bot.send_chat_action(chat_id, 'upload_audio')
    print(f"Downloading audio from: {url}")
    with youtube_dl.YoutubeDL() as ydl:
        info_dict = ydl.extract_info(url, download=False)
        title = info_dict.get('title', None)
        sanitized_title = sanitize_filename(title)
        ext = 'mp3'
        audio_name = f"{sanitized_title}.{ext}"
        # Download the audio file
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{sanitized_title}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            # Check if the downloaded file is within the allowed size limit
            file_size = os.path.getsize(audio_name)
            if file_size > MAX_FILE_SIZE:
                new_name = f'{sanitized_title}_{str(uuid.uuid4())}.{ext}'
                new_name = new_name.replace(' ', '+') # replace space with '+'
                os.rename(audio_name, os.path.join('/var/www/html', new_name))
                audio_url = f'{base_url}{new_name}'
                caption = f"{sanitized_title}\n{channel_id}"
                bot.send_message(chat_id, f"حجم فایل درخواستی بالاتر از 50 مگابایت است، لطفا از طریق این لینک دانلود کنید: {audio_url}")
            else:
                caption = f"{sanitized_title}\n{channel_id}"
                with open(audio_name, 'rb') as audio:
                    bot.send_audio(chat_id, audio, caption=caption)
            # Remove the downloaded file if it exists
            if os.path.exists(audio_name):
                os.remove(audio_name)

def has_audio(format):
    command = [
        'ffprobe',
        '-v', 'error',
        '-print_format', 'json',
        '-show_streams',
        format['url']
    ]
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT)
        info = json.loads(output)
        for stream in info.get('streams', []):
            if stream.get('codec_type') == 'audio':
                return True
        return False
    except subprocess.CalledProcessError as e:
        return False

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "سلام! لطفا لینک یوتیوب را ارسال کنید")

@bot.message_handler(content_types=['text'])
def handle_message(message):
    chat_id = message.chat.id
    if not is_user_in_channel(chat_id):
        send_join_channel_message(chat_id)
        return
    video_url = message.text
    if not is_valid_youtube_url(video_url):
        bot.reply_to(message, "لینک ارسال شده اشتباه است❌ لطفا لینک صحیح مربوط به یوتیوب را ارسال کنید")
        return
    current_time = time.time()
    if chat_id in last_message_time and current_time - last_message_time[chat_id] < 20:
        remaining_time = int(20 - (current_time - last_message_time[chat_id]))
        bot.reply_to(message, f"لطفا {remaining_time} ثانیه دیگر صبر کنید ⏳")
        return
    last_message_time[chat_id] = current_time
    bot.send_message(chat_id, "درحال بررسی لینک ⏳")
    formats = get_youtube_formats(video_url)
    if not formats:
        bot.reply_to(message, "لینک ارسال شده اشتباه است❌ لطفا لینک صحیح مربوط به یوتیوب را ارسال کنید")
        return
    formats = sorted(formats, key=lambda x: (-x.get('height', -9999), -(x.get('filesize', -9999) or float('inf')), x['ext']))
    with_audio, without_audio = separate_formats_with_without_audio(formats)
    # Cache the formats for the chat_id
    video_formats_cache[chat_id] = {
        'with_audio': with_audio,
        'without_audio': without_audio
    }
    url_id = str(uuid.uuid4())
    video_urls[url_id] = video_url
    markup = types.InlineKeyboardMarkup(row_width=2)
    with_audio_button = types.InlineKeyboardButton(text="ویدیو با صدا 🎬🔉", callback_data=f"with_audio|{url_id}")
    without_audio_button = types.InlineKeyboardButton(text="ویدیو بدون صدا 🎬", callback_data=f"without_audio|{url_id}")
    audio_320kbps_button = types.InlineKeyboardButton(text="صدا با کیفیت 320kbps 🎧", callback_data=f"audio_320kbps|{url_id}")
    markup.add(with_audio_button, without_audio_button, audio_320kbps_button)
    bot.send_message(chat_id, "لطفا یک گزینه را انتخاب کنید: ", reply_markup=markup)

def show_formats(chat_id, message_id, url_id, formats):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for format in formats:
        button_text = f"{format.get('height', 'unknown')}p {format['ext']}"
        button_data = f"{format['format_id']}|{url_id}"
        button = types.InlineKeyboardButton(text=button_text, callback_data=button_data)
        buttons.append(button)
    back_button = types.InlineKeyboardButton(text="Back", callback_data=f"back|{url_id}")
    buttons.append(back_button)
    markup.add(*buttons)
    bot.edit_message_text("لطفا کیفیت مورد نظر را انتخاب کنید:", chat_id, message_id, reply_markup=markup)

def show_audio_options(chat_id, message_id, url_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    with_audio_button = types.InlineKeyboardButton(text="ویدیو با صدا 🎬🔉", callback_data=f"with_audio|{url_id}")
    without_audio_button = types.InlineKeyboardButton(text="ویدیو بدون صدا 🎬", callback_data=f"without_audio|{url_id}")
    audio_320kbps_button = types.InlineKeyboardButton(text="صدا با کیفیت 320kbps 🎧", callback_data=f"audio_320kbps|{url_id}")
    markup.add(with_audio_button, without_audio_button)
    markup.add(audio_320kbps_button)
    bot.edit_message_text("لطفا یک گزینه را انتخاب کنید:", chat_id, message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    action, url_id = call.data.split('|')
    if action not in ("back", "with_audio", "without_audio"):
        current_time = time.time()
        if chat_id in last_action_time and current_time - last_action_time[chat_id] < 20:
            remaining_time = int(20 - (current_time - last_action_time[chat_id]))
            bot.answer_callback_query(call.id, f"لطفا {remaining_time} ثانیه دیگر صبر کنید ⏳", show_alert=True)
            return
        last_action_time[chat_id] = current_time
    url = video_urls.get(url_id)
    if not url:
        bot.send_message(chat_id, "لینک مورد نظر یافت نشد❌ لطفا لینک را مجدد ارسال کنید")
        return
    if chat_id in video_formats_cache:
        cached_formats = video_formats_cache[chat_id]
        with_audio = cached_formats['with_audio']
        without_audio = cached_formats['without_audio']
    else:
        bot.send_message(chat_id, "لینک مورد نظر یافت نشد❌ لطفا لینک را مجدد ارسال کنید")
        return
    if action == "with_audio":
        if not is_user_in_channel(chat_id):
            send_join_channel_message(chat_id)
            return
        show_formats(chat_id, message_id, url_id, with_audio)
    elif action == "without_audio":
        if not is_user_in_channel(chat_id):
            send_join_channel_message(chat_id)
            return
        show_formats(chat_id, message_id, url_id, without_audio)
    elif action == "back":
        if not is_user_in_channel(chat_id):
            send_join_channel_message(chat_id)
            return
        show_audio_options(chat_id, message_id, url_id)
    elif action == "audio_320kbps":
        if not is_user_in_channel(chat_id):
            send_join_channel_message(chat_id)
            return
        download_and_send_audio(chat_id, url)
    else:
        format_id = action
        if not is_user_in_channel(chat_id):
            send_join_channel_message(chat_id)
            return
        download_and_send_video(chat_id, url, format_id)

bot.polling()
