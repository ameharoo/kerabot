# Ameharu 2021 (https://ameha.ru/)
# Make in shell: pip install python-telegram-bot requests psutils

import datetime
import json
import os
import platform
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer  # python3
import sys
from timeit import default_timer as timer
import psutil as psutil
import requests as requests
from telegram.ext import Updater, CommandHandler
from datetime import datetime

class BotDB(object):
    filename = "bot.json"

    def __init__(self):
        if not os.path.exists(BotDB.filename):
            value = "{}"
        else:
            with open(BotDB.filename, "r") as f:
                value = f.read()

        self.values = json.loads(value)

    def get(self):
        return self.values

    def save(self):
        with open(BotDB.filename, "w") as f:
            f.write(json.dumps(self.values))

    def __del__(self):
        self.save()


class ResponseCode:
    OK = [200, "OK"]
    FAIL = [500, "FAIL"]
    NOT_VALID_FORMAT = [400, "NOT_VALID_FORMAT"]
    SERVER_CANT_RECOGNIZE_COMMAND = [500, "SERVER_CANT_RECOGNIZE_COMMAND"]
    NOT_AUTHORIZED = [401, "NOT_AUTHORIZED"]


class API:
    VERSION = "1.1"
    @staticmethod
    def prepare_response(status, response):
        return {"status": status, "response": response}

    @staticmethod
    def execute(action, args):
        db = BotDB()

        if action == "ping":
            return API.prepare_response(ResponseCode.OK, f"pong:v{API.VERSION}")
        if "secret" not in args or args["secret"] != db.values["SECRET"]:
            return API.prepare_response(ResponseCode.NOT_AUTHORIZED, "Specify special secret")
        if action == "exchange":
            if "step" not in args:
                return API.prepare_response(ResponseCode.SERVER_CANT_RECOGNIZE_COMMAND, "Specify step")
            if args["step"] == "start":
                API.exchangeStartTime = datetime.now()
                Bot.send_to_all("Обмен начат.", updater, db.values["allows"], "Обмен")
                return API.prepare_response(ResponseCode.OK, "It's ok")
            if args["step"] == "end":
                Bot.send_to_all(
                    f"Обмен окончен. ({str(datetime.now() - API.exchangeStartTime) if hasattr(API, 'exchangeStartTime') else 'время неизвестно'})",
                    updater,
                    db.values["allows"],
                    "Обмен"
                )
                return API.prepare_response(ResponseCode.OK, "It's ok")
            if args["step"] == "error":
                Bot.send_to_all(f"При обмене произошла ошибка: {args['text']}", updater, db.values["allows"], "Обмен")
                return API.prepare_response(ResponseCode.OK, "It's ok")

            return API.prepare_response(ResponseCode.SERVER_CANT_RECOGNIZE_COMMAND, "Unknown step")
        if action == "notify":
            if "text" not in args:
                return API.prepare_response(ResponseCode.SERVER_CANT_RECOGNIZE_COMMAND, "Specify text")

            Bot.send_to_all(args["text"], updater, db.values["allows"], args["title"] if "title" in args else "Уведомление")
            return API.prepare_response(ResponseCode.OK, "It's ok")
        if action == "info":
            info = {
                "system": platform.system(),
                "processor": platform.processor(),
                "cpu_usage": psutil.cpu_percent(interval=1),
                "ram_total": str(round(psutil.virtual_memory().total / (1024.0 ** 3), 2)) + " GB",
                "ram_available": str(round(psutil.virtual_memory().available / (1024.0 ** 3), 2)) + " GB",
                "hdd_total": str(round(psutil.disk_usage('/').total / (1024.0 ** 3), 2)) + " GB",
                "hdd_free": str(round(psutil.disk_usage('/').free / (1024.0 ** 3), 2)) + " GB",
                "system_time": str(datetime.now())
            }
            return API.prepare_response(ResponseCode.OK, info)
        if action == "exec":
            if len(args) < 1 or "command" not in args:
                return API.prepare_response(ResponseCode.NOT_VALID_FORMAT, "Specify \"command\" argument")

            output = ""
            try:
                output = subprocess.check_output(args["command"], stderr=subprocess.STDOUT, timeout=30, shell=True)
            except Exception as e:
                return API.prepare_response(ResponseCode.FAIL, str(e))
            return API.prepare_response(ResponseCode.OK, output.decode("utf-8"))

        return API.prepare_response(ResponseCode.SERVER_CANT_RECOGNIZE_COMMAND,
                                    f"Server can't recognize your command \"{str(action)}\"")

    @staticmethod
    def get_response_from_servers(servers, action, _args):
        db = BotDB()
        args = {"secret": db.values["SECRET"]}
        args.update(_args)

        result = []

        for server in servers:
            time_start = timer()
            try:
                req = requests.post(f"http://{server}/", data=json.dumps({"action": action, "args": args}))
                d = req.json()
                d.update({"_server": server, "_delta": timer() - time_start})
                result.append(d)
            except Exception as e:
                pass

        return result


class Bot:
    def __init__(self, updater):
        self.db = BotDB()
        self.updater = updater

    def register_events(self):
        self.updater.dispatcher.add_handler(CommandHandler('stat', self.stat))
        self.updater.dispatcher.add_handler(CommandHandler('exec', self.exec))
        self.updater.dispatcher.add_handler(CommandHandler('ping', self.ping))

    @staticmethod
    def get_chunks(x, chunk_size):
        chunks, chunk_size = len(x), chunk_size
        return [x[i:i + chunk_size] for i in range(0, chunks, chunk_size)]

    @staticmethod
    def send_to_all(message, updater, chats, title=""):
        for _id in chats:
            Bot.send(_id, updater, f"*{title}*\n`{message}`")

    @staticmethod
    def send(_id, context, message):
        for c in Bot.get_chunks(message, 2000):
            try:
                context.bot.send_message(chat_id=_id, text=c, parse_mode="markdown")
            except Exception:
                pass

    def is_auth(self, _id):
        return "allows" in self.db.values and _id in self.db.values["allows"]

    def auth_with(self, id):
        if not self.is_auth(id):
            self.updater.bot.send_message(chat_id=id, text="Я вас не знаю")
            return False
        return True

    def add_admin(self, id):
        if "allows" in self.db.values:
            self.db.values["allows"].append(id)
        self.db.save()

    def stat(self, update, context):
        if not self.auth_with(update.message.from_user.id):
            return

        def make_format(response):
            names = {
                "system": "Система",
                "processor": "Процессор",
                "cpu_usage": "Использование CPU",
                "ram_total": "Всего RAM",
                "ram_available": "Доступно RAM",
                "hdd_total": "Всего HDD",
                "hdd_free": "Доступно HDD",
                "system_time": "Системное время"
            }
            if response["status"][0] != 200:
                return f"{response['_server']} => Ошибка({response['status'][1]}): {json.loads(response['response'])}"
            return f"*{response['_server']}*\n\n" + \
                   "\n".join(map(lambda x: f"*{names[x[0]]}*:  `{x[1]}`", response["response"].items()))

        results = API.get_response_from_servers(self.db.values["SERVERS"], "info", {})
        formatted = "\n\n\n".join(map(make_format, results))
        Bot.send(update.effective_chat.id, context, formatted)

    def exec(self, update, context):
        if not self.auth_with(update.message.from_user.id):
            return

        args = update.message.text.split(" ")[1:]

        if len(args) < 1:
            Bot.send(update.effective_chat.id, context,
                     "укажите адрес сервера: /exec <ip:host> <какая-то команда и аргументы>")
            return

        command = " ".join(args[1:])
        result = API.get_response_from_servers([args[0]], "exec", {"command": command})
        formatted = "\n".join(map(lambda x: f"*{x['_server']}*:\n`{x['response']}`", result))
        Bot.send(update.effective_chat.id, context, formatted)

    def ping(self, update, context):
        if not self.auth_with(update.message.from_user.id):
            return

        result = API.get_response_from_servers(self.db.values["SERVERS"], "ping", {})
        formatted = "\n".join(map(lambda x: f"*{x['_server']}*: `{x['response']}` ({round(x['_delta']*1000, 2)} мс)", result))
        Bot.send(update.effective_chat.id, context, formatted)


class HandleRequests(BaseHTTPRequestHandler):
    def _set_headers(self, code):
        self.send_response(code)
        self.send_header('Content-type', 'text/html')
        self.send_header('Server', 'Kera slave')
        self.end_headers()

    def do_GET(self):
        self._set_headers(403)
        self.wfile.write("<div style='text-align:center;'><h1>403 Forbidden</h1></div><hr><span style='font-size:16px;'>Powered by Ameharu 2021</span>".encode("utf-8"))

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


_db = BotDB()
updater = Updater(token=_db.values["TOKEN"], use_context=True)
bot = Bot(updater)

if len(sys.argv) >= 2 and sys.argv[1] == "master":
    bot.register_events()
    updater.start_polling()
    HTTPServer((_db.values["HOST"], _db.values["PORT"]), HandleRequests).serve_forever()
elif len(sys.argv) >= 2 and sys.argv[1] == "slave":
    HTTPServer((_db.values["HOST"], _db.values["PORT"]), HandleRequests).serve_forever()
else:
    print("Укажите тип запускаемого агента, добавив аргумент, например: python3 kera.py <master или slave>")
