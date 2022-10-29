from __future__ import annotations
from dataclasses import dataclass
from typing import List
import requests
from bs4 import BeautifulSoup, Tag
import re
import io
import urllib

import telebot
from telebot import types

from config import BOT_TOKEN

HOTPLAYER_URL = "https://hub.hitplayer.ru/?s={query}&p={page}" # yes, hitplayer
API_TOKEN = BOT_TOKEN
ID_REGEX = re.compile(r"id-[0-9a-f]{21}")

@dataclass
class Track:
    author: str
    title: str
    duration: int
    dl_link: str
    
    @staticmethod
    def from_tag(tag: Tag) -> Track:
        author = tag.select_one(".title > a").get_text()
        title = tag.select_one(".title > .tt").get_text()
        raw_duration = tag.select_one(".dur").get_text().split(":")
        duration = int(raw_duration[0])*60+int(raw_duration[1])
        dl_link = tag.select_one(".com > .dwnld").get("href")
        return Track(author, title, duration, dl_link)
        

def get_songs(query: str) -> List[Track]:
    print("getting songs..")
    url = HOTPLAYER_URL.format(query=query, page=1)
    req = requests.get(url)
    results = BeautifulSoup(req.text, 'lxml').find("div", class_="result")
    if results.find("p") is not None: # contains the "not found" message
        return []
    to_process = list(results.find_all("div", id=ID_REGEX))
    if results.find("div", id="pagination") is not None: # if there are more pages
        for i in range(2,6): # up to 5
            req = requests.get(HOTPLAYER_URL.format(query=query, page=i))
            results = BeautifulSoup(req.text, 'lxml').find("div", class_="result")
            to_process += list(results.find_all("div", id=ID_REGEX))
    
    tracks = [Track.from_tag(s) for s in to_process]
    return tracks
    



def download(client, message):
    print("processing..")
    app = None
    # await app.send_message(message.from_user.id, "procecececececececececessssssinG")
    # download_link = download_links[0].get('href')
    # song_req = requests.get(download_link + "?play")
    # # removes hotplayer watermark from the filename
    # new_filename = urllib.parse.unquote(song_req.headers['Content-Disposition'].partition('filename=')[2]).replace(' (www.hotplayer.ru)', '') 
    # print(new_filename)
    # audio = io.BytesIO(song_req.content)
    # await app.send_audio(
    #         message.from_user.id,
    #         audio,
    #         file_name=new_filename
    # )
