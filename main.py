import sys

import vlc
import datetime
import base64
import time
from io import BytesIO
from tkinter import DISABLED, StringVar, ACTIVE, WORD, Scale, messagebox, \
    scrolledtext, ttk, font, HORIZONTAL, VERTICAL, Label, scrolledtext, END
from ttkthemes import ThemedTk
from PIL import Image, ImageTk
import chat
import find_vod
import _constants

# Python version check: Need 3.7 +
if not sys.version_info.major == 3 and sys.version_info.minor >= 7:
    sys.exit(1)


# Config window class.
class ConfigWindow(ThemedTk):
    def __init__(self):

        # Setting theme "equinox" for config window.
        super().__init__(theme="equilux")

        # Setting config window size.
        self.minsize(width=350, height=100)

        # Making the window non-resizeable.
        self.resizable(False, False)

        # Setting config window name.
        self.title("VODPlayer Config")

        # Setting config window background color.
        self['background'] = "#464646"

        # Launching function for positioning widgets on a config window.
        self.ui_creating()

    # Positioning widgets on a config window.
    def ui_creating(self):
        # Creating entry box.
        self.entry = ttk.Entry(self)

        # Creating buttons.
        self.button_srch = ttk.Button(self, text="Search", command=self.callback, takefocus=0)
        self.button_play = ttk.Button(self, text="Play", command=self.vod_setting, state=DISABLED,takefocus=0)

        # Creating variable for OptionMenu.
        self.resVar = StringVar(self)
        self.typeVar = StringVar(self)

        # Creating resolution OptionMenu.
        self.res_list = ["", "160p30", "360p30", "480p30", "720p60", "1080p60"]
        self.res_setting = ttk.OptionMenu(self, self.resVar, *self.res_list)
        self.resVar.set(self.res_list[-1])

        self.type_list = ["", "Highlight", "Archive", "Upload"]
        self.type_setting = ttk.OptionMenu(self, self.typeVar, *self.type_list)
        self.typeVar.set(self.type_list[2])

        # Positioning widgets in the config window.
        self.res_setting.place(relx=.72, rely=.021, relwidth=.2555, relheight=.145)
        self.button_play.place(relx=.73, rely=.83)
        self.entry.place(relx=.02, rely=.02, relwidth=.4, relheight=.145)
        self.button_srch.place(relx=0.45, rely=.02)
        self.type_setting.place(relx=.72, rely=.21, relwidth=.2555, relheight=.1475)

        # Setting focus on entry box.
        self.entry.focus_set()

    def callback(self):
        # Creating list of VOD objects.
        self.vodlst = find_vod.vod_list_creater(str(self.entry.get()), self.typeVar.get().lower())

        # Looking for error, if channel is invalid.
        if type(self.vodlst) != list:
            messagebox.showinfo("VODPlayer", f" {self.vodlst}")
            return
        # Making "Play" button active.
        self.button_play["state"] = ACTIVE

        # Creating VOD's OptionMenu.
        self.vodlst.insert(0, "")
        self.vodVar = StringVar(self)
        self.vod_setting = ttk.OptionMenu(self, self.vodVar, *self.vodlst)
        if len(self.vodlst) > 1:
            self.vodVar.set(self.vodlst[1])

        # Positioning VOD's OptionMenu in the config window.
        self.vod_setting.place(relx=.02, rely=.21, relwidth=.67)

    def vod_setting(self):
        # Getting resolution value.
        vodlink_res = self.resVar.get()
        if vodlink_res == "1080p60":
            vodlink_res = "chunked"

        # Creating dict of VOD objects of channel: voddict[VOD name] = VOD object .
        self.voddict = {}
        for vd in self.vodlst[1:]:
            vd.vod_link = vd.vod_link.format(res_fps=vodlink_res)
            self.voddict[vd.__str__()] = vd

        # Creating Player window.
        Player(self.voddict[self.vodVar.get()])

        # End of config window loop.
        self.destroy()


class Player(ThemedTk):
    def __init__(self, vod):
        # Setting up Player window.
        super().__init__(theme="equilux")
        self.geometry("1280x720")
        self.title(vod.vod_name)
        self.minsize(width=1000, height=650)

        # Decoding "Play" icon from _constants.
        self.decodec_play = Image.open(BytesIO(base64.b64decode(_constants.play_icon)))
        self.decodec_fullscrean = Image.open(BytesIO(base64.b64decode(_constants.fullscrean_icon)))
        self.decodec_cinema = Image.open(BytesIO(base64.b64decode(_constants.cinema_icon)))
        self.play_icon = ImageTk.PhotoImage(master=self, image=self.decodec_play)
        self.cinema_icon = ImageTk.PhotoImage(master=self, image=self.decodec_cinema)
        self.fullscrean_icon = ImageTk.PhotoImage(master=self, image=self.decodec_fullscrean)
        self.iconbitmap('icon.ico')
        self.last_request = []
        self.printed = []
        self.vod = vod
        self.poslenght = 0
        self.guiupdate_rate = 100
        self.thread_status = True
        self.oncinemamode = False
        self.onfullscrean = False
        self.forgotten = int(time.time())

        chat.linking_images(self.vod)

        self.setup_ui()
        self.vlc_setup()
        self.after(self.guiupdate_rate, func=self.gui_update)

    def setup_ui(self):

        self.console = scrolledtext.ScrolledText(self, width=50, height=50,
                                                 state='disable', font=("roobert", 11),
                                                 wrap=WORD, borderwidth=0,
                                                 highlightthickness=0)

        self.pause_button = ttk.Button(self, image=self.play_icon, command=self.play_pause,takefocus = 0)
        self.cinemamodebt = ttk.Button(self, image=self.cinema_icon, command=self.cinemamode_cb,takefocus = 0)
        self.fullscreanmodebt = ttk.Button(self, image=self.fullscrean_icon, command=self.fullscrean_cb,takefocus = 0)

        self.scal = Scale(self, orient=HORIZONTAL, length=373, from_=0,
                          to=1, resolution=0.0001, sliderlength=10, fg="#f0f0f0",
                          borderwidth=0, highlightthickness=0)

        self.vol_scal = Scale(self, orient=HORIZONTAL, length=80,
                              from_=0, to=100, resolution=1, sliderlength=10, fg="#f0f0f0",
                              borderwidth=0, highlightthickness=0)

        self.player_frame = Label(self)
        self.timelabel = Label(self)

        self.vseparator = ttk.Separator(self, orient=VERTICAL)
        self.hseparator = ttk.Separator(self, orient=HORIZONTAL)

        self.speed_list = ["x0.2", "x0.5", "x1", "x1.2", "x1.5", "x2"]
        self.speedVar = StringVar(self)
        self.speedVar.set(self.speed_list[2])
        self.speed_setting = ttk.OptionMenu(self, self.speedVar, self.speed_list[2], *self.speed_list)

        self.console['background'] = "#18181b"
        self['background'] = "#464646"
        self.scal['background'] = "#464646"
        self.scal['foreground'] = "#464646"
        self.vol_scal['background'] = "#464646"
        self.vol_scal['foreground'] = "#464646"
        self.timelabel['background'] = "#464646"
        self.timelabel['foreground'] = "#c8c8c8"
        self.timelabel["text"] = "0:00:00/0:00:00"
        self.scal.bind("<B1-Motion>", self.get_navscale_motion)
        self.scal.bind("<ButtonRelease-1>", self.get_navscale_release)
        self.bind("<KeyRelease-Left>", self.left_realese)
        self.bind("<KeyRelease-Right>", self.right_realese)
        self.bind("<Left>", self.left_press)
        self.bind("<Right>", self.right_press)
        self.bind('<Escape>', self.anymodeoff)

        self.vol_scal.bind("<ButtonRelease-1>", self.get_volscale_release)
        self.bind("<space>", lambda event: vlc.libvlc_media_player_pause(self.player))
        self.vol_scal.set(100)

        # Packing

        self.to_defultnavbar()

    def vlc_setup(self):

        # VLC player creating
        self.Instance = vlc.Instance(["--sout-livehttp-caching"])
        self.player = self.Instance.media_player_new()
        self.media = self.Instance.media_new(self.vod.vod_link)

        self.player.set_media(self.media)
        vlc.libvlc_audio_set_volume(self.player, 100)
        self.player.set_hwnd(self.player_frame.winfo_id())

        self.player.play()

    def gui_update(self):
        if self.thread_status:
            if vlc.libvlc_media_player_is_playing(self.player) == 1:
                timecode = int(vlc.libvlc_media_player_get_time(self.player) // 1000) - 1
                if self.speedVar.get() in ["x2", "x1.2", "x1.5"]:
                    self.mes_dict_reader(timecode - 1)
                self.mes_dict_reader(timecode)
            self.after(self.guiupdate_rate, func=self.gui_update)

    def mes_dict_reader(self, timecode):
        if timecode > 0:
            if self.poslenght == 0:
                if vlc.libvlc_media_player_get_length(self.player) != 0:
                    self.lenght = vlc.libvlc_media_player_get_length(self.player) + (1 / 10 * 8)
                    self.formatedlen = str(datetime.timedelta(milliseconds=self.lenght))[:7]
                    self.poslenght = float(str(10000 / vlc.libvlc_media_player_get_length(self.player))[:10])

            if len(self.last_request) > 0:
                if timecode < self.last_request[0]["content_offset_seconds"] or \
                        timecode > self.last_request[-1]["content_offset_seconds"]:
                    if timecode > self.first_mess_timecode:
                        self.last_request = chat.message_dict(timecode, self)
                else:
                    for mes in self.last_request:
                        if int(mes["content_offset_seconds"]) == timecode:
                            if mes['_id'] not in self.printed:
                                self.print_mess(chat.Comments(mes, self))
                                self.printed.append(mes['_id'])
                        elif int(mes["content_offset_seconds"]) > timecode:
                            break
            else:
                self.first_mess_timecode = int(chat.message_dict(0, self, 1))
                self.last_request = chat.message_dict(self.first_mess_timecode, self)

            # UI updating
            time_sign = vlc.libvlc_media_player_get_time(self.player)
            formated = str(datetime.timedelta(milliseconds=time_sign))[:7]
            abs_coord_x = self.winfo_pointerx() - self.winfo_rootx()
            abs_coord_y = self.winfo_pointery() - self.winfo_rooty()
            self.motioncheck(abs_coord_x, abs_coord_y)
            self.timelabel["text"] = f"{formated}/{self.formatedlen}"
            self.scal.set(time_sign / self.lenght)
            if self.player.get_rate() != float(self.speedVar.get()[1:]):
                self.player.set_rate(float(self.speedVar.get()[1:]))

    def print_mess(self, mess):

        self.console.configure(state='normal')
        self.console.insert(END, mess.formated_time() + " ", 'timesign')
        self.console.tag_config('timesign', foreground='#C0C0C0')

        for badge in mess.userbadges:
            if type(badge) != str:
                self.console.image_create(END, image=badge)
                self.console.insert(END, " ")

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
        if vlc.libvlc_media_player_is_playing(self.player) == 1:
            vlc.libvlc_media_player_pause(self.player)

    def get_navscale_release(self, event):
        vlc.libvlc_media_player_set_position(self.player, self.scal.get())
        if vlc.libvlc_media_player_is_playing(self.player) == 0:
            vlc.libvlc_media_player_pause(self.player)

    def get_volscale_release(self, event):
        vlc.libvlc_audio_set_volume(self.player, self.vol_scal.get())

    def play_pause(self):
        vlc.libvlc_media_player_pause(self.player)

    def right_press(self, event):
        if vlc.libvlc_media_player_is_playing(self.player) == 1:
            self.get_navscale_motion("<B1-Motion>")
        self.scal.set(self.scal.get() + self.poslenght)

    def left_press(self, event):
        if vlc.libvlc_media_player_is_playing(self.player) == 1:
            self.get_navscale_motion("<B1-Motion>")
        self.scal.set(self.scal.get() - self.poslenght)

    def left_realese(self, event):
        if vlc.libvlc_media_player_is_playing(self.player) == 1:
            self.get_navscale_motion("<B1-Motion>")
        self.scal.set(self.scal.get() - self.poslenght)
        self.get_navscale_release("<ButtonRelease-1>")

    def right_realese(self, event):
        if vlc.libvlc_media_player_is_playing(self.player) == 1:
            self.get_navscale_motion("<B1-Motion>")
        self.scal.set(self.scal.get() + self.poslenght)
        self.get_navscale_release("<ButtonRelease-1>")

    def cinemamode_cb(self):
        if self.oncinemamode:
            self.attributes("-fullscreen", False)
            self.oncinemamode = False
            self.to_defultnavbar()

        else:
            self.attributes("-fullscreen", True)
            self.oncinemamode = True
            self.onfullscrean = False
            self.player_frame.place(x=0, y=0, relwidth=.78, relheight=1)
            self.pause_button.place_forget()
            self.vol_scal.place_forget()
            self.scal.place_forget()
            self.timelabel.place_forget()
            self.cinemamodebt.place_forget()
            self.fullscreanmodebt.place_forget()
            self.speed_setting.place_forget()
            self.hseparator.place_forget()
            self.console.place_forget()
            self.vseparator.place_forget()
            self.forgotten = 0
        self.motioncheck()

    def fullscrean_cb(self):
        if self.onfullscrean:
            self.attributes("-fullscreen", False)
            self.onfullscrean = False
            self.to_defultnavbar()

        else:
            self.attributes("-fullscreen", True)
            self.onfullscrean = True
            self.oncinemamode = False

            self.player_frame.place(x=0, y=0, relwidth=1, relheight=1)
            self.pause_button.place_forget()
            self.vol_scal.place_forget()
            self.scal.place_forget()
            self.timelabel.place_forget()
            self.cinemamodebt.place_forget()
            self.fullscreanmodebt.place_forget()
            self.speed_setting.place_forget()
            self.hseparator.place_forget()
            self.console.place_forget()
            self.vseparator.place_forget()
            self.forgotten = 0
        self.motioncheck()

    def anymodeoff(self, event):
        self.attributes("-fullscreen", False)
        if self.onfullscrean:
            self.fullscrean_cb()
        elif self.oncinemamode:
            self.cinemamode_cb()

    def motioncheck(self, x="check", y="check"):
        if x == "check":
            x = self.winfo_width() * 0.785 - 1
            y = self.winfo_height() - 1
        if not self.onfullscrean:
            if 0 < x < self.winfo_width() * 0.785 and self.winfo_height() * 0.925 < y < self.winfo_height():
                self.to_defultnavbar()
                self.forgotten = int(time.time())
            elif int(time.time()) - self.forgotten >= 2 and self.forgotten != 0:
                self.player_frame.place(x=0, y=0, relwidth=.78, relheight=1)
                self.pause_button.place_forget()
                self.vol_scal.place_forget()
                self.scal.place_forget()
                self.timelabel.place_forget()
                self.cinemamodebt.place_forget()
                self.fullscreanmodebt.place_forget()
                self.speed_setting.place_forget()
                self.hseparator.place_forget()
                self.forgotten = 0
        else:
            if self.winfo_height() * 0.925 < y < self.winfo_height():
                self.player_frame.place(x=0, y=0, relwidth=1, relheight=0.94)
                self.pause_button.place(relx=.005, rely=0.95, relwidth=.03875, relheight=.04)
                self.vol_scal.place(relx=.0525, rely=0.9375, relwidth=.05, relheight=.1)
                self.scal.place(relx=.1175, rely=0.9375, relwidth=.685, relheight=.1)
                self.timelabel.place(relx=.81, rely=0.9475, relwidth=.06, relheight=0.05)
                self.cinemamodebt.place(relx=.8735, rely=0.95, relwidth=.0325, relheight=.04)
                self.fullscreanmodebt.place(relx=.9085, rely=0.95, relwidth=.0325, relheight=.04)
                self.speed_setting.place(relx=.9435, rely=0.95, relwidth=.0515, relheight=.04)
                self.hseparator.place(relx=0, rely=.94, relwidth=1, relheight=0.003)
                self.forgotten = int(time.time())

            elif int(time.time()) - self.forgotten >= 2 and self.forgotten != 0:
                self.player_frame.place(x=0, y=0, relwidth=1, relheight=1)
                self.pause_button.place_forget()
                self.vol_scal.place_forget()
                self.scal.place_forget()
                self.timelabel.place_forget()
                self.cinemamodebt.place_forget()
                self.fullscreanmodebt.place_forget()
                self.speed_setting.place_forget()
                self.hseparator.place_forget()
                self.console.place_forget()
                self.vseparator.place_forget()
                self.forgotten = 0

    def to_defultnavbar(self):
        self.player_frame.place(x=0, y=0, relwidth=.78, relheight=.94)
        self.pause_button.place(relx=.005, rely=0.95, relwidth=.03875, relheight=.04)
        self.vol_scal.place(relx=.0525, rely=0.935, relwidth=.05, relheight=.1)
        self.scal.place(relx=.1175, rely=0.935, relwidth=.465, relheight=.1)
        self.timelabel.place(relx=.5885, rely=0.9475, relwidth=.06, relheight=0.05)
        self.cinemamodebt.place(relx=.6525, rely=0.95, relwidth=.0325, relheight=.04)
        self.fullscreanmodebt.place(relx=.6875, rely=0.95, relwidth=.0325, relheight=.04)
        self.speed_setting.place(relx=.7225, rely=0.95, relwidth=.0515, relheight=.04)
        self.hseparator.place(relx=0, rely=.94, relwidth=.78, relheight=0.003)
        self.console.place(relx=.782, rely=0, relwidth=.218, relheight=1)
        self.vseparator.place(relx=.78, rely=0, relwidth=0.001, relheight=1)

    def on_closing(self):
        self.thread_status = False
        vlc.libvlc_media_player_stop(self.player)
        self.destroy()


def main():
    debug = False
    if debug:
        vod = find_vod.vod_list_creater("shroud", "archive")[0]
        vod.vod_link = vod.vod_link.format(res_fps="chunked")
        mainplayer = Player(vod)
    else:
        mainplayer = ConfigWindow()
    mainplayer.mainloop()
    sys.exit(7)


if __name__ == '__main__':
    main()
