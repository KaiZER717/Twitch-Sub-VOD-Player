import datetime
import sys
import tkinter.font as tkFont
from os import path
from sys import version_info
from tkinter import *
from tkinter import scrolledtext, ttk
from ttkthemes import ThemedTk
from PIL import Image, ImageTk
import vlc
import sys, os
import chat
import find_vod

if not version_info.major == 3 and version_info.minor >= 7:
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
        self.minsize(width=1000, height=650)
        self.font_tp = tkFont.Font(family="roobert", size=11)
        self.play_icon = ImageTk.PhotoImage(master=self, file="icon.png")
        self.title(vod.vod_name)
        self.thread_status = True

        self.vod = vod
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

        self.console['background'] = "#464646"
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
        self.console.place(relx=.785, rely=0, relwidth=.215, relheight=1)
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
        self.downloaded = False
        self.after(20, func=self.gui_update)

    def gui_update(self):
        if self.thread_status:
            self.player_frame.focus()
            # Player playing media
            if vlc.libvlc_media_player_is_playing(self.player) == 1:
                # Chat window updating
                messages = chat.message_dict(self.vod)
                if messages == "path error":
                    self.on_closing()
                if not self.downloaded:
                    if path.exists(messages[1]):
                        self.downloaded = True
                messages = messages[0]
                timecode = str(int(vlc.libvlc_media_player_get_time(self.player) // 1000) - 1)
                if timecode in messages:
                    if len(messages[timecode]) != 1:
                        for mes1 in messages[timecode]:
                            if mes1.key not in self.printed:
                                self.print_mess(mes1)
                                self.printed.append(mes1.key)
                    else:
                        if messages[timecode][0].key not in self.printed:
                            self.print_mess(messages[timecode][0])
                            self.printed.append(messages[timecode][0].key)

                # UI updating
                time_sign = vlc.libvlc_media_player_get_time(self.player)
                lenght = vlc.libvlc_media_player_get_length(self.player) + (1 / 10 * 8)
                formated = str(datetime.timedelta(milliseconds=time_sign))[:7]
                self.timelabel["text"] = formated
                self.scal.set(time_sign / lenght)
                self.player.set_rate(float((self.speedVar.get())[1:]))

            self.after(20, func=self.gui_update)

    def print_mess(self, mess):
        self.console.configure(state='normal')  # enable insert
        self.console.insert(END, str(mess.timesign) + " ", 'timesign')
        self.console.tag_config('timesign', foreground='#C0C0C0')
        self.console.insert(END, str(mess.sender), str(mess.sender))
        self.console.tag_config(str(mess.sender), foreground=mess.colour)
        self.console.insert(END, ": ", 'mess')
        self.console.insert(END, str(mess.mess) + "\n", 'mess')
        self.console.tag_config('mess', foreground='#FFFFFF')
        self.console.yview(END)  # autoscroll
        self.console.configure(state='disabled')  # disable editing

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
        vlc.libvlc_media_player_pause(self.player)

    def on_closing(self):
        self.thread_status = False
        vlc.libvlc_media_player_stop(self.player)
        self.destroy()


def main():
    mainplayer = MainApplication()
    mainplayer.mainloop()
    sys.exit(7)


if __name__ == '__main__':
    main()
