import sys
import os

import vlc
import datetime
import base64
from io import BytesIO

from tkinter import *
import tkinter.font as tkFont
from tkinter import scrolledtext, ttk
from ttkthemes import ThemedTk
import tkinter.messagebox as mb
from PIL import Image, ImageTk

import chat
import find_vod
import _constants

if not sys.version_info.major == 3 and sys.version_info.minor >= 7:
    sys.exit(1)


class MainApplication(ThemedTk):
    def __init__(self):
        super().__init__(theme="equilux")
        self.minsize(width=350, height=100)
        self.resizable(False, False)
        self.title("VODPlayer Config")
        self.ui_creating()

    def ui_creating(self):
        self['background'] = "#464646"
        self.entery = ttk.Entry(self)

        self.button_srch = ttk.Button(self, text="Search", command=self.callback)
        self.button_play = ttk.Button(self, text="Play", command=self.vod_setting, state=DISABLED)

        self.resVar = StringVar()

        self.res_list = ["", "160p30", "360p30", "480p30", "720p60", "1080p60"]
        self.res_setting = ttk.OptionMenu(self, self.resVar, *self.res_list)
        self.resVar.set(self.res_list[-1])

        self.res_setting.place(relx=.72, rely=.021, relwidth=.25, relheight=.145)
        self.button_play.place(relx=.73, rely=.83)
        self.entery.place(relx=.02, rely=.02, relwidth=.4, relheight=.145)
        self.button_srch.place(relx=0.45, rely=.02)
        self.entery.focus_set()

    def callback(self):

        self.vodVar = StringVar()
        vodlink_res = self.resVar.get()
        if vodlink_res == "1080p60":
            vodlink_res = "chunked"

        self.vodlst = find_vod.vod_list_creater(str(self.entery.get()), vodlink_res)
        if type(self.vodlst) != list:
            mb.showinfo("VODPlayer", f"  {self.vodlst}")
            self.entery.delete(0, 'end')
            return

        self.voddict = {}
        for vd in self.vodlst:
            self.voddict[vd.__str__()] = vd

        self.button_play["state"] = ACTIVE

        self.vod_setting = ttk.OptionMenu(self, self.vodVar, *self.vodlst)
        self.vod_setting.place(relx=.02, rely=.25, relwidth=.67)

    def vod_setting(self):
        Child(self.voddict[self.vodVar.get()])
        self.destroy()


class Child(ThemedTk):
    def __init__(self, vod):
        super().__init__(theme="equilux")
        self.geometry("1280x720")
        self.title(vod.vod_name)
        self.minsize(width=1000, height=650)
        self.font_tp = tkFont.Font(family="roobert", size=11)

        self.decodec_image = Image.open(BytesIO(base64.b64decode(_constants.encoded_icon)))
        self.play_icon = ImageTk.PhotoImage(master=self, image=self.decodec_image)
        self.last_request = []
        self.vod = vod
        self.thread_status = True

        self.setup_ui()
        self.vlc_setup()

    def setup_ui(self):

        self.console = scrolledtext.ScrolledText(self, width=50, height=50,
                                                 state='disable', font=self.font_tp,
                                                 wrap=WORD, borderwidth=0,
                                                 highlightthickness=0)

        self.pause_button = ttk.Button(self, image=self.play_icon, command=self.play_pause)

        self.scal = Scale(self, orient=HORIZONTAL, length=373, from_=0,
                          to=1, resolution=0.0001, sliderlength=10, fg="#f0f0f0",
                          borderwidth=0, highlightthickness=0)

        self.vol_scal = Scale(self, orient=HORIZONTAL, length=80,
                              from_=0, to=100, resolution=1, sliderlength=10,
                              borderwidth=0, highlightthickness=0)

        self.timelabel = Label(self)
        self.vseparator = ttk.Separator(self, orient=VERTICAL)
        self.hseparator = ttk.Separator(self, orient=HORIZONTAL)
        self.player_frame = Label(self)

        self.speedVar = StringVar()
        self.speed_list = ["", "x0.25", "x0.5", "x1", "x1.5", "x2"]
        self.speedVar.set(self.speed_list[3])
        self.speed_setting = ttk.OptionMenu(self, self.speedVar, *self.speed_list)

        self.console['background'] = "#18181b"
        self['background'] = "#464646"
        self.scal['background'] = "#464646"
        self.scal['foreground'] = "#464646"
        self.vol_scal['background'] = "#464646"
        self.vol_scal['foreground'] = "#c8c8c8"
        self.timelabel['background'] = "#464646"
        self.timelabel['foreground'] = "#c8c8c8"
        self.scal.bind("<B1-Motion>", self.get_navscale_motion)
        self.scal.bind("<ButtonRelease-1>", self.get_navscale_release)

        self.vol_scal.bind("<ButtonRelease-1>", self.get_volscale_release)
        self.bind("<space>", lambda event: vlc.libvlc_media_player_pause(self.player))
        self.vol_scal.set(100)

        # Packing

        self.player_frame.place(x=0, y=0, relwidth=.78, relheight=.94)
        self.pause_button.place(x=5, rely=0.95, relwidth=.05, relheight=.04)
        self.vol_scal.place(relx=.08, rely=0.94, relwidth=.05, relheight=.1)
        self.scal.place(relx=.15, rely=0.94, relwidth=.5, relheight=.1)
        self.timelabel.place(relx=.65, rely=0.953, relwidth=.06, relheight=0.05)
        self.speed_setting.place(relx=.71, rely=0.953, relwidth=.05, relheight=.04)
        self.hseparator.place(relx=0, rely=.94, relwidth=.78, relheight=0.003)
        self.console.place(relx=.782, rely=0, relwidth=.215, relheight=1)
        self.vseparator.place(relx=.78, rely=0, relwidth=0.001, relheight=1)

    def vlc_setup(self):
        # VLC player creating
        self.Instance = vlc.Instance()
        self.player = self.Instance.media_player_new()
        self.media = self.Instance.media_new(self.vod.vod_link)
        self.player.set_media(self.media)
        vlc.libvlc_audio_set_volume(self.player, 100)
        self.player.set_hwnd(self.player_frame.winfo_id())
        self.player.play()
        self.printed = []

        self.after(200, func=self.gui_update)

    def gui_update(self):
        if self.thread_status:
            timecode = int(vlc.libvlc_media_player_get_time(self.player) // 1000) - 1
            if self.speedVar.get() in ["x2", "x1.5"]:
                self.mes_dict_reader(timecode - 1)
            self.mes_dict_reader(timecode)
        self.after(200, func=self.gui_update)

    def mes_dict_reader(self, timecode):
        if vlc.libvlc_media_player_is_playing(self.player) == 1:
            if timecode > 0:
                if len(self.last_request) > 0:
                    if timecode < self.last_request[0].sec_offset or timecode > self.last_request[-1].sec_offset:
                        if timecode > self.first_mess_timecode:
                            self.last_request = chat.message_dict(timecode, self)
                    else:
                        for mes in self.last_request:
                            if mes.sec_offset == timecode:
                                if mes.comment_id not in self.printed:
                                    self.print_mess(mes)
                                    self.printed.append(mes.comment_id)
                else:
                    self.first_mess_timecode = int(chat.message_dict(0, self, 1))
                    self.last_request = chat.message_dict(self.first_mess_timecode, self)

            # UI updating
            time_sign = vlc.libvlc_media_player_get_time(self.player)
            lenght = vlc.libvlc_media_player_get_length(self.player) + (1 / 10 * 8)
            formated = str(datetime.timedelta(milliseconds=time_sign))[:7]
            self.timelabel["text"] = formated
            self.scal.set(time_sign / lenght)
            self.player.set_rate(float((self.speedVar.get())[1:]))

    def print_mess(self, mess):

        self.console.configure(state='normal')
        self.console.insert(END, mess.formated_time() + " ", 'timesign')
        self.console.tag_config('timesign', foreground='#C0C0C0')

        for badge in mess.userbadges:
            if type(badge) != str:
                self.console.image_create(END, image=badge)

        self.console.insert(END, mess.username, mess.username)
        self.console.tag_config(mess.username, foreground=mess.usercolor)

        if not mess.isaction:
            self.console.insert(END, ": ", 'mess')

        for fragment in mess.msg:
            if type(fragment) == str:
                self.console.insert(END, f" {fragment}", 'mess')
            else:
                self.console.image_create(END, image=fragment)
        self.console.insert(END, '\n')
        self.console.tag_config('mess', foreground='#FFFFFF')

        self.console.yview(END)  # autoscroll
        self.console.configure(state='disabled')

    def get_navscale_motion(self, event):
        if vlc.libvlc_media_player_is_playing(self.player):
            vlc.libvlc_media_player_pause(self.player)

    def get_navscale_release(self, event):
        vlc.libvlc_media_player_set_position(self.player, self.scal.get())
        if not vlc.libvlc_media_player_is_playing(self.player):
            vlc.libvlc_media_player_pause(self.player)

    def get_volscale_release(self, event):
        vlc.libvlc_audio_set_volume(self.player, self.vol_scal.get())

    def play_pause(self):
        self.player_frame.focus()
        vlc.libvlc_media_player_pause(self.player)

    def on_closing(self):
        self.thread_status = False
        vlc.libvlc_media_player_stop(self.player)
        self.destroy()


def main():
    debug = False
    if not debug:
        mainplayer = MainApplication()
    else:
        mainplayer = Child(find_vod.vod_list_creater("shroud")[1])
    mainplayer.mainloop()
    sys.exit(7)


if __name__ == '__main__':
    main()
