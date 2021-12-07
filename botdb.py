import json
import os
import platform


class BotDB(object):
    filename = ""

    def __init__(self):
        if platform.system().lower() == "linux":
            BotDB.filename = "/etc/kera/kera.config.json"
        else:
            BotDB.filename = "kera.config.json"

        if not os.path.exists(BotDB.filename):
            raise Exception(f"Файл конфига не найден. Путь: \"{BotDB.filename}\"")
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
