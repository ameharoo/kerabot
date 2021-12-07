import json

from telegram.ext import CommandHandler

from api import API
from botdb import BotDB


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

    def send_to_all(self, message, chats=None, title=""):
        if chats is None:
            chats = self.db.values["allows"]

        for _id in chats:
            self.send(_id, f"*{title}*\n`{message}`")

    def send(self, _id, message):
        for c in Bot.get_chunks(message, 2000):
            try:
                self.updater.bot.send_message(chat_id=_id, text=c, parse_mode="markdown")
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
                return f"{response['_server']} => Ошибка({response['status'][1]}): {json.dumps(response['response'])}"
            return f"*{response['_server']}*\n\n" + \
                   "\n".join(map(lambda x: f"*{names[x[0]]}*:  `{x[1]}`", response["response"].items()))

        results = API.get_response_from_servers(self.db.values["SERVERS"], "info", {})
        formatted = "\n\n\n".join(map(make_format, results))
        self.send(update.effective_chat.id, formatted)

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
        self.send(update.effective_chat.id, formatted)

    def ping(self, update, context):
        if not self.auth_with(update.message.from_user.id):
            return

        result = API.get_response_from_servers(self.db.values["SERVERS"], "ping", {})
        formatted = "\n".join(
            map(lambda x: f"*{x['_server']}*: `{x['response']}` ({round(x['_delta'] * 1000, 2)} мс)", result))
        self.send(update.effective_chat.id, formatted)
