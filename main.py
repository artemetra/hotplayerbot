from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import List, Tuple
import requests
from bs4 import BeautifulSoup, Tag
import re
import io
from io import BufferedIOBase

# for some reason, just importing urllib provides no typehints
from urllib import parse as urllib_parse

from telebot.async_telebot import AsyncTeleBot
from telebot import types

from config import BOT_TOKEN

bot = AsyncTeleBot(BOT_TOKEN, parse_mode="html")
HOTPLAYER_URL = "https://box.hitplayer.ru/?s={query}&p={page}"  # yes, hitplayer
ID_REGEX = re.compile(r"id-[0-9a-f]{21}")


@dataclass
class Track:
    author: str
    title: str
    duration: int
    dl_link: str

    @staticmethod
    def from_tag(tag: Tag) -> Track:
        """Constructs a Track from a bs4 tag"""
        author = tag.select_one(".title > a").get_text()
        title = tag.select_one(".title > .tt").get_text()
        raw_duration = tag.select_one(".dur").get_text().split(":")
        duration = int(raw_duration[0]) * 60 + int(raw_duration[1])
        dl_link = tag.select_one(".com > .dwnld").get("href") + "?play"
        return Track(author, title, duration, dl_link)

    def download(self) -> Tuple[str, io.BytesIO]:
        """Returns the tuple with the new filename and the audio content"""
        song_req = requests.get(self.dl_link)
        audio = io.BytesIO(song_req.content)
        # removes hotplayer watermark from the filename
        original_filename = urllib_parse.unquote(
            song_req.headers["Content-Disposition"].partition("filename=")[-1]
        )
        new_filename = original_filename.replace(" (www.hotplayer.ru)", "")

        return new_filename, audio


def get_tracks(query: str) -> List[Track]:
    print("getting tracks..")
    url = HOTPLAYER_URL.format(query=query, page=1)
    req = requests.get(url)
    results = BeautifulSoup(req.text, "lxml").find("div", class_="result")
    if results.find("p") is not None:  # contains the "not found" message
        return []
    to_process = list(results.find_all("div", id=ID_REGEX))
    if results.find("div", id="pagination") is not None:  # if there are more pages
        for i in range(2, 6):  # up to 5
            req = requests.get(HOTPLAYER_URL.format(query=query, page=i))
            results = BeautifulSoup(req.text, "lxml").find("div", class_="result")
            to_process += list(results.find_all("div", id=ID_REGEX))

    tracks = [Track.from_tag(s) for s in to_process]
    return tracks



@bot.message_handler(commands=["start"])
async def send_welcome(message):
    await bot.reply_to(
        message,
        "Send me a search query and I'll reply with a track. I only work in private messages.",
    )


@bot.inline_handler(lambda _: True)
async def display_results(inline_query: types.InlineQuery):
    tracks = get_tracks(inline_query.query)
    if not tracks:
        not_found = [types.InlineQueryResultArticle(
            '1',
            'not_found',
            types.InputTextMessageContent('nothing found')
        )]
        await bot.answer_inline_query(inline_query.id, not_found, cache_time=1)
        return

    results = [
        types.InlineQueryResultAudio(
            idx,
            audio_url=track.dl_link,
            title=track.title,
            performer=track.author,
            audio_duration=track.duration,
        )
        for idx, track in enumerate(tracks)
    ]
    await bot.answer_inline_query(inline_query.id, results[:10], cache_time=1)

@bot.message_handler(
    func=lambda message: True, content_types=["text"], chat_types=["private"]
)
async def download(message: types.Message):
    await bot.send_message(message.chat.id, "processing...")
    tracks = get_tracks(message.text)
    if not tracks:
        await bot.send_message(message.chat.id, "Track not found :(")
        return
    track = tracks[0]
    await bot.send_message(
        message.chat.id,
        "Sending <pre>" + track.author + " - " + track.title + "</pre>...",
    )
    filename, audio = track.download()
    await bot.send_audio(
        message.from_user.id,
        audio,
        performer=track.author,
        title=track.title,
        duration=track.duration,
    )


asyncio.run(bot.polling())
