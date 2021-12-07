# Ameharu 2021 (https://ameha.ru/)
# Make in shell: pip install python-telegram-bot requests psutils

import datetime
import json
import os
import platform
import subprocess
import time
from http.server import BaseHTTPRequestHandler, HTTPServer  # python3
import sys
from threading import Thread
from timeit import default_timer as timer
import psutil as psutil
import requests as requests
import telegram
from telegram.ext import CommandHandler
from datetime import datetime

from api import API, ResponseCode
from bot import Bot
from botdb import BotDB
from updater import Updater


class HandleRequests(BaseHTTPRequestHandler):
    def _set_headers(self, code):
        self.send_response(code)
        self.send_header('Content-type', 'text/html')
        self.send_header('Server', 'Kera slave')
        self.end_headers()

    def do_GET(self):
        self._set_headers(403)
        self.wfile.write(
            "<div style='text-align:center;'><h1>403 Forbidden</h1></div><hr><span style='font-size:16px;'>Powered by Ameharu 2021</span>".encode(
                "utf-8"))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        raw_data = self.rfile.read(content_length)
        print(f"POST {datetime.now()} {raw_data}")
        post_data = json.loads(raw_data)  # <--- Gets the data itself

        if not isinstance(post_data, dict) or "action" not in post_data or "args" not in post_data:
            self._set_headers(ResponseCode.NOT_VALID_FORMAT[0])
            self.wfile.write(
                json.dumps(API.prepare_response(ResponseCode.NOT_VALID_FORMAT, "Not valid format")).encode("utf-8"))
            return

        result = API.execute(post_data["action"], post_data["args"])
        self._set_headers(result["status"][0])
        self.wfile.write(json.dumps(result).encode("utf-8"))

    def do_PUT(self):
        self.do_POST()


if len(sys.argv) >= 2 and sys.argv[1] == "install":
    Updater(None).check_updates(True)
    sys.exit(0)

_db = BotDB()
updater = telegram.ext.Updater(token=_db.values["TOKEN"], use_context=True)
bot = Bot(updater)

github_updater = Updater(bot)


def check_updates(is_master):
    while True:
        github_updater.check_updates(master=is_master)
        time.sleep(60)


if len(sys.argv) >= 2 and sys.argv[1] == "master":
    bot.register_events()
    updater.start_polling()
    Thread(target=check_updates, args=(True,)).start()
    HTTPServer((_db.values["HOST"], _db.values["PORT"]), HandleRequests).serve_forever()
elif len(sys.argv) >= 2 and sys.argv[1] == "slave":
    Thread(target=check_updates, args=(False,)).start()
    HTTPServer((_db.values["HOST"], _db.values["PORT"]), HandleRequests).serve_forever()
else:
    print("Укажите тип запускаемого агента, добавив аргумент, например: python3 kera.py <master или slave>")
