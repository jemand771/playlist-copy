import os

import pyyoutube


def make_youtube_api():
    return pyyoutube.Api(
        client_id=os.environ["YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["YOUTUBE_CLIENT_SECRET"]
    )


def httpsify_url(url):
    # securr
    if url.startswith("http://"):
        return "https://" + url.removeprefix("http://")
    return url
