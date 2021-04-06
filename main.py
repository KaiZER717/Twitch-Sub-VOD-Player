import sys

import vlc
import datetime
import base64
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
        self.button_srch = ttk.Button(self, text="Search", command=self.callback)
        self.button_play = ttk.Button(self, text="Play", command=self.vod_setting, state=DISABLED)

        # Creating variable for resolution's OptionMenu.
        self.resVar = StringVar()

        # Creating resolution OptionMenu.
        self.res_list = ["", "160p30", "360p30", "480p30", "720p60", "1080p60"]
        self.res_setting = ttk.OptionMenu(self, self.resVar, *self.res_list)
        self.resVar.set(self.res_list[-1])

        # Positioning widgets in the config window.
        self.res_setting.place(relx=.72, rely=.021, relwidth=.25, relheight=.145)
        self.button_play.place(relx=.73, rely=.83)
        self.entry.place(relx=.02, rely=.02, relwidth=.4, relheight=.145)
        self.button_srch.place(relx=0.45, rely=.02)

        # Setting focus on entry box.
        self.entry.focus_set()

    def callback(self):
        # Creating list of VOD objects.
        self.vodlst = find_vod.vod_list_creater(str(self.entry.get()))

        # Looking for error, if channel is invalid.
        if type(self.vodlst) != list:
            messagebox.showinfo("VODPlayer", f" {self.vodlst}")
            return
        # Making "Play" button active.
        self.button_play["state"] = ACTIVE

        # Creating VOD's OptionMenu.
        self.vodVar = StringVar(self)
        self.vod_setting = ttk.OptionMenu(self, self.vodVar, *self.vodlst)

        # Positioning VOD's OptionMenu in the config window.
        self.vod_setting.place(relx=.02, rely=.25, relwidth=.67)

    def vod_setting(self):
        # Getting resolution value.
        vodlink_res = self.resVar.get()
        if vodlink_res == "1080p60":
            vodlink_res = "chunked"

        # Creating dict of VOD objects of channel: voddict[VOD name] = VOD object .
        self.voddict = {}
        for vd in self.vodlst:
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
        self.decodec_image = Image.open(BytesIO(base64.b64decode(_constants.encoded_icon)))
        self.play_icon = ImageTk.PhotoImage(master=self, image=self.decodec_image)

        self.last_request = []
        self.printed = []
        self.vod = vod
        self.poslenght = 0
        self.guiupdate_rate = 500
        self.thread_status = True
        chat.linking_images(self.vod)

        self.setup_ui()
        self.vlc_setup()
        self.after(self.guiupdate_rate, func=self.gui_update)

    def setup_ui(self):

        self.console = scrolledtext.ScrolledText(self, width=50, height=50,
                                                 state='disable', font=("roobert", 11),
                                                 wrap=WORD, borderwidth=0,
                                                 highlightthickness=0)

        self.pause_button = ttk.Button(self, image=self.play_icon, command=self.play_pause)

        self.scal = Scale(self, orient=HORIZONTAL, length=373, from_=0,
                          to=1, resolution=0.0001, sliderlength=10, fg="#f0f0f0",
                          borderwidth=0, highlightthickness=0)

        self.vol_scal = Scale(self, orient=HORIZONTAL, length=80,
                              from_=0, to=100, resolution=1, sliderlength=10,
                              borderwidth=0, highlightthickness=0)

        self.player_frame = Label(self)
        self.timelabel = Label(self)

        self.vseparator = ttk.Separator(self, orient=VERTICAL)
        self.hseparator = ttk.Separator(self, orient=HORIZONTAL)

        self.speed_list = ["x0.25", "x0.5", "x1", "x1.25", "x1.5", "x2"]
        self.speedVar = StringVar(self)
        self.speedVar.set(self.speed_list[2])
        self.speed_setting = ttk.OptionMenu(self, self.speedVar, self.speed_list[2], *self.speed_list)

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
        self.bind("<KeyRelease-Left>", self.left_realese)
        self.bind("<KeyRelease-Right>", self.right_realese)
        self.bind("<Left>", self.left_press)
        self.bind("<Right>", self.right_press)

        self.vol_scal.bind("<ButtonRelease-1>", self.get_volscale_release)
        self.bind("<space>", lambda event: vlc.libvlc_media_player_pause(self.player))
        self.vol_scal.set(100)

        # Packing

        self.player_frame.place(x=0, y=0, relwidth=.78, relheight=.94)
        self.pause_button.place(x=5, rely=0.95, relwidth=.05, relheight=.04)
        self.vol_scal.place(relx=.08, rely=0.94, relwidth=.05, relheight=.1)
        self.scal.place(relx=.15, rely=0.94, relwidth=.5, relheight=.1)
        self.timelabel.place(relx=.65, rely=0.953, relwidth=.06, relheight=0.05)
        self.speed_setting.place(relx=.71, rely=0.953, relwidth=.0525, relheight=.04)
        self.hseparator.place(relx=0, rely=.94, relwidth=.78, relheight=0.003)
        self.console.place(relx=.782, rely=0, relwidth=.218, relheight=1)
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

    def gui_update(self):
        if self.thread_status:
            if vlc.libvlc_media_player_is_playing(self.player) == 1:
                timecode = int(vlc.libvlc_media_player_get_time(self.player) // 1000) - 1
                if self.speedVar.get() in ["x2", "x1.25", "x1.5"]:
                    self.mes_dict_reader(timecode - 1)
                self.mes_dict_reader(timecode)
            self.after(self.guiupdate_rate, func=self.gui_update)

    def mes_dict_reader(self, timecode):
        if timecode > 0:
            if self.poslenght == 0:
                if vlc.libvlc_media_player_get_length(self.player) != 0:
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
        lenght = vlc.libvlc_media_player_get_length(self.player) + (1 / 10 * 8)
        formated = str(datetime.timedelta(milliseconds=time_sign))[:7]
        self.timelabel["text"] = formated
        self.scal.set(time_sign / lenght)
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
        self.player_frame.focus()
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

    def on_closing(self):
        self.thread_status = False
        vlc.libvlc_media_player_stop(self.player)
        self.destroy()


def main():
    debug = False
    if debug:
        vod = find_vod.vod_list_creater("shroud")[1]
        vod.vod_link = vod.vod_link.format(res_fps="chunked")
        mainplayer = Player(vod)
    else:
        mainplayer = ConfigWindow()
    mainplayer.mainloop()
    sys.exit(7)


if __name__ == '__main__':
    main()
