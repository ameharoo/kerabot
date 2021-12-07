import os
import platform
import sys
import zipfile

import psutil
import requests


class Updater:

    def __init__(self, bot):
        self.bot = bot

        self.__sha = None
        self.bin_path = "."
        self.config_path = "."
        self.sha_path = os.path.join(self.config_path, ".sha")

        if platform.system().lower() == "linux":
            self.bin_path = "/usr/bin/kera"
            self.config_path = "/etc/kera"

            if not os.path.exists(self.config_path):
                os.mkdir(self.config_path)
            if not os.path.exists(self.bin_path):
                os.mkdir(self.bin_path)
            if not os.path.exists(self.sha_path):
                print("Notice: sha file of current version not found ", file=sys.stderr)
            else:
                self.__sha = open(self.sha_path, "r").read()

        else:
            print("Заметьте, что поддержка обновлений может некорректно работать ", file=sys.stderr)


    def check_updates(self, force=False):
        last_commit = requests.get("https://api.github.com/repos/ameharoo/kerabot/commits/master").json()
        if force or (self.__sha is not None and last_commit["sha"] != self.__sha):
            if not force:
                self.bot.send_to_all(
                    f"Предложено обновление. Дата: {last_commit['commit']['author']['date']}\n" +
                    f"Автор: @{last_commit['author']['login']}\n" +
                    f"Описание: {last_commit['commit']['message']}\n" +
                    f"SHA: {last_commit['sha']}\n" +
                    f"Обновление будет выполнено автоматически\n" +
                    f"URL: {last_commit['html_url']}\n",
                    title="🆙 Входящее обновление"
                )
            self.update(last_commit["sha"], force)

    def update(self, new_sha, force):
        sha_zip = f"{new_sha}.zip"
        new_bin_dir = os.path.join(self.bin_path, new_sha)
        const_bin_dir = os.path.join(self.bin_path, "bin")

        if not force:
            self.bot.send_to_all(
                f"Происходит обновление файлов. Бот временно не отвечает на запросы.",
                title="🔄0️⃣ Входящее обновление"
            )
        else:
            print(f"Происходит обновление файлов.")

        url = f"https://api.github.com/repos/ameharoo/kerabot/zipball/{new_sha}"
        response = requests.get(url)
        if response.status_code == 200:
            with open(sha_zip, 'wb') as f:
                f.write(response.content)

        if not force:
            self.bot.send_to_all(
                "",
                title="🔄1️⃣ Файлы загружены"
            )
        else:
            print("Файлы загружены")

        with zipfile.ZipFile(sha_zip, "r") as zip_ref:
            if not os.path.exists(new_bin_dir):
                os.mkdir(new_bin_dir)
            zip_ref.extractall(new_bin_dir)

        os.remove(sha_zip)

        if not force:
            self.bot.send_to_all(
                "",
                title="🔄2️⃣ Распаковка завершена"
            )
        else:
            print("Распаковка завершена")

        if os.path.islink(const_bin_dir):
            os.unlink(const_bin_dir)

        os.symlink(os.path.join(new_bin_dir, os.listdir(new_bin_dir)[0]), const_bin_dir)

        open(self.sha_path, "w").write(new_sha)

        if not force:
            self.bot.send_to_all(
                "",
                title="🔄3️⃣ Установка символьных ссылок успешна"
            )

            self.bot.send_to_all(
                "",
                title="✅ Обновление установлено"
            )

            self.restart()
        else:
            print("Обновление установлено")

    def restart(self):
        os.execl(sys.executable, sys.executable, *sys.argv)
