import json
import platform
import subprocess
from datetime import datetime

import psutil
import requests

from botdb import BotDB
from timeit import default_timer as timer

from updater import Updater


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
        global bot
        db = BotDB()

        if action == "ping":
            return API.prepare_response(ResponseCode.OK, f"pong:v{API.VERSION}")
        if "secret" not in args or args["secret"] != db.values["SECRET"]:
            return API.prepare_response(ResponseCode.NOT_AUTHORIZED, "Specify special secret")
        if action == "sha_version":
            return API.prepare_response(ResponseCode.NOT_AUTHORIZED, "Specify special secret")
        if action == "exchange":
            if "step" not in args:
                return API.prepare_response(ResponseCode.OK, Updater(None).get_sha())
            if args["step"] == "start":
                API.exchangeStartTime = datetime.now()
                bot.send_to_all("Обмен начат.", db.values["allows"], "Обмен")
                return API.prepare_response(ResponseCode.OK, "It's ok")
            if args["step"] == "end":
                bot.send_to_all(
                    f"Обмен окончен. ({str(datetime.now() - API.exchangeStartTime) if hasattr(API, 'exchangeStartTime') else 'время неизвестно'})",
                    db.values["allows"],
                    "Обмен"
                )
                return API.prepare_response(ResponseCode.OK, "It's ok")
            if args["step"] == "error":
                bot.send_to_all(f"При обмене произошла ошибка: {args['text']}", db.values["allows"], "Обмен")
                return API.prepare_response(ResponseCode.OK, "It's ok")

            return API.prepare_response(ResponseCode.SERVER_CANT_RECOGNIZE_COMMAND, "Unknown step")
        if action == "notify":
            if "text" not in args:
                return API.prepare_response(ResponseCode.SERVER_CANT_RECOGNIZE_COMMAND, "Specify text")

            bot.send_to_all(args["text"], db.values["allows"],
                            args["title"] if "title" in args else "Уведомление")
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
                result.append({"_server": server,
                               "_error": True,
                               "_delta": -0.01,
                               "status": [0, "Exception"],
                               "response": str(e)})

        return result
