from googleapiclient.discovery import build
import pandas as pd
import re
import os
import isodate  # pip install isodate
from datetime import datetime

"""
code ref from:
    https://youtu.be/5qtC-tsQ-wE?si=GS6tgHveLg5LWXLN
    https://youtu.be/th5_9woFJmk?si=MkIsYa3wzbBna-45
"""

'''
for getting vidwo with filter by changing
    duration
        =>  MIN/MAX_DURATION_SEC variable
    title keywords
        => # KEYWORDS section
        => classify_title(title) function
           modify the default return value to match the channel's style
'''

API_KEY = "YOUR_API_KEY"

# ==========================
# CONFIG
# ==========================
CHANNEL_IDS = [                 # HERE: (change) channel ID
    "UCYvmuw-JtVrTZQ-7Y4kd63Q"
]

BASE_OUTPUT_NAME = "KatyPerry"  # (optional change) filename 
STYLE = "EN"                    # HERE: (change) style

# Duration limits in seconds
MIN_DURATION_SEC = 60 * 1  # 2 minute
MAX_DURATION_SEC = 60 * 8  # 7 minutes

unwanted_keywords = [
    "promotional video", "pv", "teaser", "tralier", "trailer","vlog",
    "ep ", " ep", "album", "reaction", "highlight", 
    "behind the scenes", "after movie", "making behind", "rehearsals"
]

# ==========================
# KEYWORDS 
# ==========================
DANCE = ['dance', 'choreography']
REMIX = ['remix']
LANG = ['ver.', ' ver ', 'edit', 'clip', 'instrumental']
COVER = ['cover']
MV = ['official', 'original', 'mv', 'm.v', 'music video', 'musicvideo', 
      'official mv', 'official m/v', 'original mv', 'original song', 
      'original sound', 'special clip']
LYRIC = ['lyric video', 'lyrics', 'lyric']
LIVE = ['live', 'live ver', 'live video', 'live clip', 'episode',
        'performance', 'special edit', 'cam',
        'stage', 'tour', 'festival', 'fanfest']
AUDIO = ['audio', 'visualizer']

# ==========================
# FUNCTIONS
# ==========================
def classify_title(title):
    title_lower = title.lower()
    if any(k in title_lower for k in DANCE):
        return "Dance"
    elif any(k in title_lower for k in AUDIO):
        return "Audio"
    elif any(k in title_lower for k in REMIX):
        return "Remix"
    elif any(k in title_lower for k in LIVE):
        return "Live"
    elif any(k in title_lower for k in LANG):
        return "LangVer"
    elif any(k in title_lower for k in LYRIC):
        return "Lyric"
    elif any(k in title_lower for k in MV):
        return "MV"
    elif any(k in title_lower for k in COVER):
        return "Cover"
    else:
        return "Unknown"  # default

def get_next_output_filename(base_name):
    """Find the next available filename with a numeric suffix."""
    if not os.path.exists(f"{base_name}.csv"):
        return f"{base_name}.csv"
    counter = 1
    while os.path.exists(f"{base_name}_{counter}.csv"):
        counter += 1
    return f"{base_name}_{counter}.csv"

def parse_duration(duration_str):
    """Convert ISO 8601 duration to seconds."""
    try:
        return int(isodate.parse_duration(duration_str).total_seconds())
    except:
        return 0

def get_day_of_week(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime("%A")  # Monday, Tuesday, etc
    except:
        return ""

def get_season(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        month = dt.month
        if month in [12, 1, 2]:
            return "Winter"
        elif month in [3, 4, 5]:
            return "Spring"
        elif month in [6, 7, 8]:
            return "Summer"
        elif month in [9, 10, 11]:
            return "Fall"
    except:
        return ""
    

# ==========================
# MAIN SCRIPT
# ==========================
def main():
    youtube = build("youtube", "v3", developerKey=API_KEY)
    rows = []

    for channel_id in CHANNEL_IDS:
        print(f"Processing channel: {BASE_OUTPUT_NAME}")

        channel_res = youtube.channels().list(
            part="contentDetails,statistics",
            id=channel_id
        ).execute()
        subs = int(channel_res['items'][0]['statistics'].get('subscriberCount', 0))
        uploads_playlist_id = channel_res['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        next_page_token = None
        while True:
            playlist_items = youtube.playlistItems().list(
                part="contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=next_page_token
            ).execute()

            video_ids = []
            for item in playlist_items["items"]:
                video_ids.append(item["contentDetails"]["videoId"])

            videos_res = youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=",".join(video_ids)
            ).execute()

            for v in videos_res["items"]:
                title = v["snippet"]["title"]
                title_lower = title.lower()

                # Skip unwanted keywords
                if any(uw in title_lower for uw in unwanted_keywords):
                    continue

                duration_str = v.get("contentDetails", {}).get("duration")
                if not duration_str:
                    continue  # skip videos without duration info

                duration_sec = parse_duration(duration_str)
                if duration_sec < MIN_DURATION_SEC or duration_sec > MAX_DURATION_SEC:
                    continue

                vtype = classify_title(title)
                if vtype == "Unknown":
                    continue

                published_at = v["snippet"].get("publishedAt", "")
                day_of_week = get_day_of_week(published_at)
                season = get_season(published_at)
                stats = v.get("statistics", {})

                # Check if all required keys exist
                if all(k in stats for k in ["viewCount", "likeCount", "commentCount"]):
                    view_count = int(stats["viewCount"])
                    like_count = int(stats["likeCount"])
                    comment_count = int(stats["commentCount"])
                else:
                    # Skip this video
                    print(f"Skipping video (missing stats): {title}")
                    continue
                engagement = (like_count + comment_count) / view_count if view_count > 0 else 0

                rows.append({
                    "style": STYLE,
                    "channelId": channel_id,
                    "channelSubs": subs,
                    "title": title,
                    "type": vtype,
                    "duration_sec": duration_sec,
                    "publishedAt": published_at,
                    "dayOfWeek": day_of_week,
                    "season": season,
                    "views": view_count,
                    "likes": like_count,
                    "comments": comment_count,
                    "engagment": engagement
                })

            next_page_token = playlist_items.get("nextPageToken")
            if not next_page_token:
                break

    all_music_videos = pd.DataFrame(rows)

    output_file = get_next_output_filename(BASE_OUTPUT_NAME)
    all_music_videos.to_csv(output_file, index=False)
    print(f"Saved {len(all_music_videos)} videos to {output_file}")

if __name__ == "__main__":
    main()