from pyrogram import Client, filters
from pyrogram.types import (InlineQueryResultArticle, InputTextMessageContent,
                            InlineKeyboardMarkup, InlineKeyboardButton)

import requests
from bs4 import BeautifulSoup
import re
import io
from urllib.parse import unquote

from config import API_ID, API_HASH, BOT_TOKEN

app = Client("hotplayerbot", API_ID, API_HASH, bot_token=BOT_TOKEN)

HOTPLAYER_URL = "https://hub.hitplayer.ru/?s={}" # yes, hitplayer

@app.on_message(filters.text & filters.private)
async def download(client: Client, message):
    print("processing..")
    await app.send_message(message.from_user.id, "procecececececececececessssssinG")
    url = HOTPLAYER_URL.format(message.text)
    req = requests.get(url)
    download_links = BeautifulSoup(req.text, 'lxml').find_all('a', class_="dwnld fa fa-download")
    #download_link = re.search(r'href="(https://d\d.hotplayer.ru/downloadm/.+)"', req.text).group(1)
    download_link = download_links[0].get('href')
    song_req = requests.get(download_link + "?play")
    new_filename = unquote(song_req.headers['Content-Disposition'].partition('filename=')[2]).replace(' (www.hotplayer.ru)', '') 
    print(new_filename)
    audio = io.BytesIO(song_req.content)
    await app.send_audio(
            message.from_user.id,
            audio,
            file_name=new_filename
    )
    

print("Running...")
app.run()  # Automatically start() and idle()

