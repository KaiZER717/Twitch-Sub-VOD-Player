import datetime
import time
import requests
import _constants
import urllib
from PIL import Image, ImageTk
import io

loaded_emotes = {}
bttv_linked_emotes = {}


class Comments:
    def __init__(self, rawcomment, root):
        self.sec_offset = int(rawcomment['content_offset_seconds'])
        self.username = rawcomment['commenter']['display_name']
        self.message = rawcomment['message']['body']

        self.isaction = rawcomment['message']['is_action']
        self.comment_id = rawcomment['_id']
        self.userbadges = {}
        self.msg = []

        if "user_color" in rawcomment['message']:
            self.usercolor = rawcomment['message']['user_color']
        else:
            self.usercolor = "#00FF7F"

        if 'user_badges' in rawcomment['message']:
            for badge in rawcomment['message']['user_badges']:
                self.userbadges[badge['_id']] = badge['version']

        if 'fragments' in rawcomment['message']:
            for fragment in rawcomment['message']['fragments']:
                if 'emoticon' in fragment:
                    self.msg.append(emote_by_id(fragment['emoticon']['emoticon_id'], root))
                else:
                    raw_lst = fragment['text'].split()
                    emote_names = list(bttv_linked_emotes.keys())
                    for word in raw_lst:
                        if word in emote_names:
                            self.msg.append(bttv_emote_by_name(word, root))
                        else:
                            self.msg.append(word)

    # formatting time: 0:00:50 to 00:50.
    def formated_time(self):
        raw_format = str(datetime.timedelta(seconds=self.sec_offset))[:7]
        if raw_format.split(":")[0] == "0":
            raw_format = raw_format[2:]
        return raw_format


# Creating list of comments in this period: len(list) = 48.
def message_dict(vod, offset, root):
    global bttv_linked_emotes
    headers = {'Accept': _constants.application,
               'Client-ID': _constants.client_id}

    # Requesting channel id from api, using channel name.
    id_req_link = f"https://api.twitch.tv/kraken/users?login={vod.channel}"
    id_req = requests.get(id_req_link, headers=headers).json()

    channel_id = id_req['users'][0]['_id']
    if len(bttv_linked_emotes) == 0:
        bttv_linked_emotes = btfz_emote_dict_by_id(channel_id, vod.channel)
    comment_req_link = f"https://api.twitch.tv/v5/videos/{vod.vod_id}/comments?content_offset_seconds={offset}"
    comments_ = requests.get(comment_req_link, headers=headers).json()["comments"]

    return [Comments(mess, root) for mess in comments_]


def emote_by_id(emote_id, root):
    global loaded_emotes
    if emote_id not in loaded_emotes:
        emmote_icon_link = f"https://static-cdn.jtvnw.net/emoticons/v2/{emote_id}/default/dark/1.0"
        raw_data = urllib.request.urlopen(emmote_icon_link).read()
        loaded_emotes[str(emote_id)] = ImageTk.PhotoImage(master=root, image=Image.open(io.BytesIO(raw_data)))
    return loaded_emotes[str(emote_id)]


def btfz_emote_dict_by_id(channel_id, channel_name):
    emote_list = {}

    ffz_comment_req_link = f"http://api.frankerfacez.com/v1/room/{channel_name}"
    ffz_emote_list_request = requests.get(ffz_comment_req_link).json()
    if "error" not in ffz_emote_list_request:
        if "sets" in ffz_emote_list_request:
            setlist = str(ffz_emote_list_request["room"]["set"])

            for emote_ffz in ffz_emote_list_request["sets"][setlist]["emoticons"]:
                emote_list[emote_ffz["name"]] = ["png", f"http:{emote_ffz['urls']['1']}"]

    comment_req_link = f"https://api.betterttv.net/3/cached/users/twitch/{channel_id}"
    emote_list_request = requests.get(comment_req_link).json()

    channels_emotes = {}
    shared_emotes = {}

    if 'channelEmotes' in emote_list_request:
        channels_emotes = emote_list_request['channelEmotes']
    if 'sharedEmotes' in emote_list_request:
        shared_emotes = emote_list_request['sharedEmotes']
    if len(channels_emotes) + len(shared_emotes) != 0:

        for emote_ in channels_emotes:
            emote_list[emote_["code"]] = [emote_["imageType"], f"https://cdn.betterttv.net/emote/{emote_['id']}/1x"]
        for emote in shared_emotes:
            emote_list[emote["code"]] = [emote["imageType"], f"https://cdn.betterttv.net/emote/{emote['id']}/1x"]

    return emote_list


def bttv_emote_by_name(emote_name, root):
    global bttv_linked_emotes, loaded_emotes
    if bttv_linked_emotes != "empty_list":
        if bttv_linked_emotes[emote_name][0] == "gif":
            if emote_name not in loaded_emotes:
                raw_data = urllib.request.urlopen(bttv_linked_emotes[emote_name][1]).read()
                loaded_emotes[emote_name] = ImageTk.PhotoImage(master=root, image=Image.open(io.BytesIO(raw_data)))
            return loaded_emotes[emote_name]
        elif bttv_linked_emotes[emote_name][0] == "png":
            if emote_name not in loaded_emotes:
                raw_data = urllib.request.urlopen(bttv_linked_emotes[emote_name][1]).read()
                loaded_emotes[emote_name] = ImageTk.PhotoImage(master=root, image=Image.open(io.BytesIO(raw_data)))
            return loaded_emotes[emote_name]
    return "empty_list"
