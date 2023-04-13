# Youtube2Download | یوتیوب تو دانلود
Youtube video and music leecher bot for Telegram
## Demo: [t.me/YT2DLbot](https://t.me/YT2DLbot)
## Install Software Dependencies:
`$ sudo apt update && apt install python3 python3-pip apache2 tmux`
## Install Required libraries:
`$ pip install uuid telebot yt-dlp `
## Create a bot
Use @BotFather to create and get a Token. open `yt2dl_en.py` OR `yt2dl_fa.py` and replace "API_TOKEN" on line 16 with your own API Token
## Sponsor Channel
After making the bot with @BotFather, made the bot an administrator in your channel (no special permission required), then open `yt2dl_en.py` OR `yt2dl_fa.py` and change `@Your_Chanel` on line 18 with your desired channel id
## Setting up URL
Leeched files that are bigger than 50MB can not be sent over telegram (Telegram's Policy) instead we use a webserver to send direct link to the user. this script uses Apache web server and `/var/www/html/` by default.

Open `yt2dl_en.py` OR `yt2dl_fa.py` and replace your server IP or Domain with `IP_OR_DOMAIN` on line 20
## Launch
`chmod +x yt2dl_start.sh`

`tmux`

`./yt2dl_start.sh`

# Credit: [ChatGPT-4](https://chat.openai.com)
