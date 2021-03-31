import datetime
import time
import requests
import _constants
from urllib.request import urlopen
from PIL import Image, ImageTk
from io import BytesIO

loaded_emotes = {}
bttv_linked_emotes = {}

linked_badges = {"subscriber": {}}
loaded_badges = {}

headers = {'Client-ID': _constants.client_id}


class Comments:
    def __init__(self, rawcomment, root):
        self.sec_offset = int(rawcomment['content_offset_seconds'])
        self.username = rawcomment['commenter']['display_name']
        self.message = rawcomment['message']['body']
        self.isaction = rawcomment['message']['is_action']
        self.comment_id = rawcomment['_id']
        self.userbadges = []
        self.msg = []
        if "user_color" in rawcomment['message']:
            self.usercolor = rawcomment['message']['user_color']
        else:
            self.usercolor = "#00FF7F"

        if 'user_badges' in rawcomment['message']:
            for badge in rawcomment['message']['user_badges']:
                self.userbadges.append(channel_badges(badge['_id'], badge['version'], root))

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


def channel_badges(_id, ver, root):
    global headers, loaded_badges, linked_badges
    if _id == "subscriber":
        badge_name = f"{_id}{ver}"
        if badge_name not in loaded_badges:
            im = Image.open(BytesIO(urlopen(linked_badges["subscriber"][str(ver)]).read()))
            loaded_badges[badge_name] = ImageTk.PhotoImage(master=root, image=im)
        return loaded_badges[badge_name]
    if _id in linked_badges:
        if _id not in loaded_badges:
            im = Image.open(BytesIO(urlopen(linked_badges[_id]).read()))
            loaded_badges[_id] = ImageTk.PhotoImage(master=root, image=im)
        return loaded_badges[_id]
    return "nondisplayed"


def badge_by_name(channel_id):
    global headers, linked_badges
    sub_badge_id_req = f'https://badges.twitch.tv/v1/badges/channels/{channel_id}/display?language=en'
    sub_bages_ids = requests.get(sub_badge_id_req, headers=headers).json()["badge_sets"]["subscriber"]["versions"]
    linked_badges = {"subscriber": {},
                     'partner': 'https://static-cdn.jtvnw.net/badges/v1/d12a2e27-16f6-41d0-ab77-b780518f00a3/1',
                     'admin': 'https://static-cdn.jtvnw.net/badges/v1/9ef7e029-4cdf-4d4d-a0d5-e2b3fb2583fe/1',
                     'broadcaster': 'https://static-cdn.jtvnw.net/badges/v1/5527c58c-fb7d-422d-b71b-f309dcb85cc1/1',
                     'glhf-pledge': 'https://static-cdn.jtvnw.net/badges/v1/3158e758-3cb4-43c5-94b3-7639810451c5/1',
                     'glitchcon2020': 'https://static-cdn.jtvnw.net/badges/v1/1d4b03b9-51ea-42c9-8f29-698e3c85be3d/1',
                     'global_mod': 'https://static-cdn.jtvnw.net/badges/v1/9384c43e-4ce7-4e94-b2a1-b93656896eba/1',
                     'hype-train': 'https://static-cdn.jtvnw.net/badges/v1/fae4086c-3190-44d4-83c8-8ef0cbe1a515/1',
                     'moderator': 'https://static-cdn.jtvnw.net/badges/v1/3267646d-33f0-4b17-b3df-f923a41db1d0/1',
                     'premium': 'https://static-cdn.jtvnw.net/badges/v1/bbbe0db0-a598-423e-86d0-f9fb98ca1933/1',
                     'staff': 'https://static-cdn.jtvnw.net/badges/v1/d97c37bd-a6f5-4c38-8f57-4e4bef88af34/1',
                     'sub-gift-leader': 'https://static-cdn.jtvnw.net/badges/v1/21656088-7da2-4467-acd2-55220e1f45ad/1',
                     'sub-gifter': 'https://static-cdn.jtvnw.net/badges/v1/f1d8486f-eb2e-4553-b44f-4d614617afc1/1',
                     'vip': 'https://static-cdn.jtvnw.net/badges/v1/b817aba4-fad8-49e2-b88a-7cc744dfa6ec/1'}
    for subbagde in sub_bages_ids:
        if len(subbagde) == 4:
            continue
        linked_badges["subscriber"][subbagde] = sub_bages_ids[subbagde]['image_url_1x']

    return linked_badges


# Creating list of comments in this period: len(list) = 48.
def message_dict(offset, root, getfirst=0):
    global bttv_linked_emotes, headers, linked_badges
    vod = root.vod
    if getfirst == 1:
        comment_req_link = f"https://api.twitch.tv/v5/videos/{vod.vod_id}/comments?"
        return requests.get(comment_req_link, headers=headers).json()["comments"][0]["content_offset_seconds"]
    if len(bttv_linked_emotes) == 0:
        bttv_linked_emotes = btfz_emote_dict_by_id(vod.channelid, vod.channel)
    if len(linked_badges) == 1:
        linked_badges = badge_by_name(vod.channelid)
    comment_req_link = f"https://api.twitch.tv/v5/videos/{vod.vod_id}/comments?content_offset_seconds={offset}"
    comments_ = requests.get(comment_req_link, headers=headers).json()["comments"]
    res = []
    for comm in comments_:
        if offset - 15 > comm["content_offset_seconds"]:
            continue
        if offset - 15 < comm["content_offset_seconds"] < offset + 15:
            res.append(Comments(comm, root))
        if offset + 15 < comm["content_offset_seconds"]:
            break

    return res


def emote_by_id(emote_id, root):
    global loaded_emotes
    if emote_id not in loaded_emotes:
        emmote_icon_link = f"https://static-cdn.jtvnw.net/emoticons/v2/{emote_id}/default/dark/1.0"
        raw_data = urlopen(emmote_icon_link).read()
        loaded_emotes[str(emote_id)] = ImageTk.PhotoImage(master=root, image=Image.open(BytesIO(raw_data)))
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
                im = Image.open(BytesIO(urlopen(bttv_linked_emotes[emote_name][1]).read()))
                loaded_emotes[emote_name] = ImageTk.PhotoImage(master=root, image=im)
            return loaded_emotes[emote_name]
        elif bttv_linked_emotes[emote_name][0] == "png":
            if emote_name not in loaded_emotes:
                im = Image.open(BytesIO(urlopen(bttv_linked_emotes[emote_name][1]).read()))
                loaded_emotes[emote_name] = ImageTk.PhotoImage(master=root, image=im)
            return loaded_emotes[emote_name]
    return "empty_list"
