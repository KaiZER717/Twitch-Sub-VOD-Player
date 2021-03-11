import datetime
import threading
import tkinter.font as tkFont
import vlc
from time import sleep
from tkinter import *
from tkinter import scrolledtext, ttk

import chat
import find_vod

if not sys.version_info.major == 3 and sys.version_info.minor >= 5:
    print("This script requires Python 3.5 or higher!")
    print(f"You are using Python {sys.version_info.major}.{sys.version_info.minor}")
    sys.exit(1)

vod = find_vod.vod_selector()


# GUI scale events com2

def get_val_motion(event):
    global scal, player
    vlc.libvlc_media_player_set_position(player, scal.get())


def get_vol_motion(event):
    global vol_scal, player
    vlc.libvlc_audio_set_volume(player, vol_scal.get())


# Stopping event

def play_pause():
    global player
    vlc.libvlc_media_player_pause(player)


# Chat time sync

def print_mess(mess):
    global console
    console.configure(state='normal')  # enable insert
    try:
        console.insert(END, str(mess.timesign) + " ", 'timesign')
        console.tag_config('timesign', foreground='#C0C0C0')
        console.insert(END, str(mess.sender), str(mess.sender))
        console.tag_config(str(mess.sender), foreground=mess.colour)
        console.insert(END, ": ", 'mess')
        console.insert(END, str(mess.mess) + "\n", 'mess')
        console.tag_config('mess', foreground='#FFFFFF')
    except:
        print(mess.mess)
    console.yview(END)  # autoscroll
    console.configure(state='disabled')  # disable editing


def chat_sync(player, vod_id):
    printed = []
    while player_playing:
        sleep(.4)
        messages = chat.message_dict(vod_id)
        if messages == "path error":
            on_closing()
        timecode = str(int(vlc.libvlc_media_player_get_time(player) // 1000) - 1)
        if timecode in messages:
            if len(messages[timecode]) != 1:
                for mes1 in messages[timecode]:
                    if mes1.key not in printed:
                        print_mess(mes1)
                        printed.append(mes1.key)
            else:
                if messages[timecode][0].key not in printed:
                    print_mess(messages[timecode][0])
                    printed.append(messages[timecode][0].key)


def player_sync():
    global scal, label

    while player_playing:
        sleep(1)
        time_sign = vlc.libvlc_media_player_get_time(player)
        lenght = vlc.libvlc_media_player_get_length(player) + (1 / 10 * 8)
        formated = str(datetime.timedelta(milliseconds=time_sign))[:7]
        label["text"] = formated
        scal.set(time_sign / lenght)


# Create main widget

root = Tk()
root.title("VOD Player")
root.geometry("1280x720")
root.minsize(width=1000, height=650)
font_tp = tkFont.Font(family="roobert", size=11)

# Create widgets

console = scrolledtext.ScrolledText(root, width=50, height=50,
                                    state='disable', font=font_tp,
                                    wrap=WORD, borderwidth=0,
                                    highlightthickness=0)
button = ttk.Button(root, text="Pause", command=play_pause)
scal = Scale(root, orient=HORIZONTAL, length=373, from_=0,
             to=1, resolution=0.005, sliderlength=10, fg="#f0f0f0",
             borderwidth=0, highlightthickness=0)
vol_scal = Scale(root, orient=HORIZONTAL, length=80,
                 from_=0, to=100, resolution=1, sliderlength=10,
                 borderwidth=0, highlightthickness=0)
player_label = Label(root)
label = Label(root)

console['background'] = "#313335"
root['background'] = "#313335"
scal['background'] = "#313335"
scal['foreground'] = "#313335"
vol_scal['background'] = "#313335"
vol_scal['foreground'] = "#c8c8c8"
label['background'] = "#313335"
label['foreground'] = "#c8c8c8"

scal.bind("<ButtonRelease-1>", get_val_motion)
vol_scal.bind("<ButtonRelease-1>", get_vol_motion)
vol_scal.set(100)

# Packing

player_label.place(x=0, y=0, relwidth=.78, relheight=.94)

button.place(x=5, rely=0.95, relwidth=.05, relheight=.04)
vol_scal.place(relx=.08, rely=0.94, relwidth=.05, relheight=.1)
scal.place(relx=.15, rely=0.94, relwidth=.5, relheight=.1)
label.place(relx=.67, rely=0.953, relwidth=.05, relheight=0.05)

console.place(relx=.78, rely=0, relwidth=.22, relheight=1)

# VLC player creating

Instance = vlc.Instance()
player = Instance.media_player_new()
media = Instance.media_new(vod.vod_link)
player.set_media(media)
player_playing = True
vlc.libvlc_audio_set_volume(player, 100)
player.set_hwnd(player_label.winfo_id())
player.play()

# Thread creating

thread_chat = threading.Thread(target=player_sync, daemon=True)
thread_chat_sync = threading.Thread(target=chat_sync, args=(player, vod.vod_id))
thread_chat_sync.start()
thread_chat.start()


def on_closing():
    global player_playing
    player_playing = False
    player.stop()
    root.destroy()
    return


root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
