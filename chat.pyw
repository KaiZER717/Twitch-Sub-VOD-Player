import getpass
import os.path
import shutil
import subprocess
import sys
import threading
import time


class Message:
    def __init__(self, timesign, sender, mess):
        self.key = sender + str(timesign)
        self.timesign = timesign
        self.sender = "".join([sender[j] for j in range(len(sender)) if ord(sender[j]) in range(65536)])
        self.mess = "".join([mess[j] for j in range(len(mess)) if ord(mess[j]) in range(65536)])
        self.colour = ["#FF0000", "#0000FF", "#FF7F50",
                       "#9ACD32", "#FF4500", "#FF4500",
                       "#5F9EA0", "#1E90FF", "#8A2BE2",
                       "#00FF7F"][int(str(len(sender) ** 2.5)[0])]

    def __str__(self):
        return f'{self.timesign} {self.sender}: {self.mess}'


def download_thread(script, log_path, rename_path):
    print("Downloading logs ...")
    download_proc = subprocess.call(script, stdout=open(os.devnull, 'wb'))
    print(f"Logs downloaded => {rename_path}")
    if not os.path.exists(rename_path):
        shutil.copyfile(log_path, rename_path)


def log_download(vod):
    executable = sys.executable.split('\\')[-2]
    tcd_path = f"C:\\Users\\{getpass.getuser()}\\AppData\\Local\\Programs\\Python\\{executable}\\Scripts\\tcd.exe"
    script_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    if not os.path.exists(f"{script_path}\\logs\\"):
        os.mkdir(f"{script_path}\\logs")
    if not os.path.exists(f"{script_path}\\logs\\{vod.channel}\\"):
        os.mkdir(f"{script_path}\\logs\\{vod.channel}")
    if not os.path.exists(f"{script_path}\\logs\\cache\\"):
        os.mkdir(f"{script_path}\\logs\\cache")
    args_ = f"-v {vod.vod_id} -o --quiet {script_path}\\logs\\cache\\"
    script = f"{tcd_path} {args_}"
    file_name = f"{vod.vod_name} [{vod.vod_date}]"
    for sym in ["\\", "|", "/", ":", "?", "*", "<", ">", '"']:
        if sym in file_name:
            file_name = file_name.replace(sym, " ")

    rename_path = f"{script_path}\\logs\\{vod.channel}\\{file_name}.txt"
    log_path = f"{script_path}\\logs\\cache\\{vod.vod_id}.txt"

    downloader = threading.Thread(target=download_thread, args=(script, log_path, rename_path))

    if not os.path.exists(log_path):
        if os.path.exists(tcd_path):
            downloader.start()
        else:
            return "path error"
    return log_path, rename_path


def message_dict(vod):
    log_path, log_named = log_download(vod)
    if log_path == "path error":
        return "path error"

    while not os.path.exists(log_path):
        time.sleep(1)
    logs = open(log_path, encoding="utf-8", errors="ignore").read().split("\n")[:-1]
    messages = {}

    for mess in logs:

        tm = mess[:9][1:8].split(":")
        tm_format = str(int(tm[0]) * 3600 + int(tm[1]) * 60 + int(tm[2]))

        if tm[0] != "0":
            time_sign = (":".join(tm))
        else:
            time_sign = (":".join(tm[1:]))

        mess_sender = mess.split(" ")[1][1:-1]
        mes = " ".join(mess.split(" ")[2:])

        if tm_format in messages:
            messages[tm_format].append(Message(time_sign, mess_sender, mes))
        else:
            messages[tm_format] = [Message(time_sign, mess_sender, mes)]

    return messages, log_named
