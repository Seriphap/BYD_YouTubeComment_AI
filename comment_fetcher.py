import requests
import pandas as pd

def get_video_title(video_id, api_key):
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet",
        "id": video_id,
        "key": api_key
    }
    response = requests.get(url, params=params).json()
    items = response.get("items", [])
    if items:
        return items[0]["snippet"]["title"]
    return "Unknown Title"

def get_all_comments(video_ids, api_key):
    def fetch_comments(video_id, video_title):
        comments = []
        url = "https://www.googleapis.com/youtube/v3/commentThreads"
        params = {
            "part": "snippet",
            "videoId": video_id,
            "key": api_key,
            "maxResults": 100,
            "textFormat": "plainText"
        }

        next_page_token = None
        while True:
            if next_page_token:
                params["pageToken"] = next_page_token
            response = requests.get(url, params=params)
            data = response.json()

            for item in data.get("items", []):
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "video_id": video_id,
                    "video_title": video_title,
                    "author": snippet["authorDisplayName"],
                    "comment": snippet["textDisplay"]
                })

            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break
        return comments

    all_comments = []
    for vid in video_ids:
        title = get_video_title(vid, api_key)
        all_comments.extend(fetch_comments(vid, title))

    df = pd.DataFrame(all_comments)
    df.to_csv("youtube_comments.csv", index=False)
    return df
