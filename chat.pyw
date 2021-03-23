import datetime
import time
import requests


class Comments:
    def __init__(self, rawcomment):
        self.sec_offset = rawcomment['content_offset_seconds']
        self.username = rawcomment['commenter']['display_name']
        self.message = rawcomment['message']['body']
        self.isaction = rawcomment['message']['is_action']
        self.comment_id = rawcomment['_id']
        self.userbadges = {}

        if "user_color" in rawcomment['message']:
            self.usercolor = rawcomment['message']['user_color']
        else:
            self.usercolor = "#00FF7F"

        if 'user_badges' in rawcomment['message']:
            for badge in rawcomment['message']['user_badges']:
                self.userbadges[badge['_id']] = badge['version']

    def formated_time(self):
        raw_format = str(datetime.timedelta(seconds=self.sec_offset))[:7]
        if raw_format.split(":")[0] == "0":
            raw_format = raw_format[2:]
        return raw_format


def message_dict(vod, offset):
    headers = {"Client-ID": '3y57z5uv1413gc7j320ljq6bpk83wy'}
    base_url = f"https://api.twitch.tv/v5/videos/{vod.vod_id}/comments?content_offset_seconds={offset}"
    comments_ = requests.get(base_url, headers=headers).json()["comments"]
    messages = []
    for mess in comments_:
        if int(mess["content_offset_seconds"]) == offset:
            messages.append(Comments(mess))

    return messages
