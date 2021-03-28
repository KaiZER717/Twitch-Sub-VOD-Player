import requests
import _constants


class Vods:
    def __init__(self, vod_id, vod_date, vod_name, vod_link, channel_name, vod_lenght, res_fps):
        msk_date = vod_date.split("T")[0]
        msk_hour = str(int(vod_date.split("T")[1].split(":")[0]) + 3)
        msk_min = vod_date.split("T")[1].split(":")[1]
        msk_sec = vod_date.split("T")[1].split(":")[2]

        self.vod_date = f"{msk_date} {msk_hour}:{msk_min}:{msk_sec[:-1]}"
        self.vod_id = vod_id[1:]
        self.vod_name = vod_name
        self.vod_link = vod_link + f"{res_fps}/index-dvr.m3u8"
        self.channel = channel_name
        self.vod_lenght = vod_lenght

    def __str__(self):
        return self.vod_name[:35] + "... | " + self.vod_date


def vod_list_creater(channel_name, res="chunked"):
    # Request headers.
    headers = {'Accept': _constants.application,
               'Client-ID': _constants.client_id}

    # Requesting channel id from api, using channel name.
    id_req_link = f"https://api.twitch.tv/kraken/users?login={channel_name}"
    id_req = requests.get(id_req_link, headers=headers).json()

    if 'error' in id_req:
        return "Invalid channel name,try again..."
    if id_req['_total'] == 0:
        return "Invalid channel name,try again..."
    channel_id = id_req['users'][0]['_id']

    # Requesting links of vods from api, using channel id.
    video_req_link = f"https://api.twitch.tv/kraken/channels/{channel_id}/videos?broadcast_type=archive&limit=100"
    video_req = requests.get(video_req_link, headers=headers).json()

    if len(dict(video_req)["videos"]) == 0:
        return "Vod list is empty,try again..."

    # Creating list of Vod objects.
    dict_resp = dict(video_req)
    vod_list = []
    for vod in dict_resp["videos"]:
        vod_lenght = int(vod['length'])
        vod_id = str(vod["_id"])
        vod_date = str(vod["created_at"])
        vod_name = str(vod["title"])
        vod_link = str(vod['seek_previews_url'].split("storyboards")[0])
        vod_list.append(Vods(vod_id, vod_date, vod_name, vod_link, channel_name, vod_lenght, res))

    return vod_list
