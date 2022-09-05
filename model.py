import enum
import uuid
from dataclasses import dataclass

import pyyoutube


@dataclass(eq=True, frozen=True)
class SizeAgeLimit:
    count: int | None = None
    age_seconds: int | None = None

    def count_as_dict_if_set(self, key="count"):
        return {} if self.count is None else {
            key: self.count
        }


class ItemBase:
    pass


class PlaylistBase:
    def __init__(self, *args, **kwargs):
        pass

    def purge(self, limit: SizeAgeLimit):
        pass

    def get_items(self, limit: SizeAgeLimit, reverse: bool = False) -> list[ItemBase]:
        pass

    def contains(self, item: ItemBase) -> bool:
        pass

    def add(self, item: ItemBase):
        pass

    def remove_at_index(self, index: int):
        pass


class YoutubeItem(ItemBase):

    def __init__(self, item: pyyoutube.PlaylistItem):
        self.item = item


class YoutubePlaylist(PlaylistBase):

    def __init__(self, api: pyyoutube.Api, playlist: pyyoutube.Playlist):
        super().__init__()
        self.api = api
        self.playlist = playlist

    def get_items(self, limit: SizeAgeLimit, reverse: bool = False) -> list[YoutubeItem]:
        return [
            YoutubeItem(item)
            for item
            in self.api.get_playlist_items(
                playlist_id=self.playlist.id,
                **limit.count_as_dict_if_set("count")
            ).items
        ]

    def purge(self, limit: SizeAgeLimit):
        pass  # TODO implement

    def contains(self, item: YoutubeItem) -> bool:
        pass  # TODO implement (via playlist item filter)

    def add(self, item: YoutubeItem):
        # self.api.BASE_URL = "https://eo51s8b0fzilp1s.m.pipedream.net/"
        r = self.api._request(
            "playlistItems",
            method="POST",
            args={
                "part": "snippet",
                "access_token": self.api._access_token
            },
            post_args={
                "snippet": {
                    "playlistId": self.playlist.id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": item.item.snippet.resourceId.videoId
                    }
                },
                "_json": True
            }
        )
        data = self.api._parse_response(r)

    def remove_at_index(self, index: int):
        pass  # TODO implement


class ApiBase:
    type: str = ""

    def __init__(self, *args, **kwargs):
        pass

    def get_user_identifier(self) -> str:
        return f"{self.type}.{self._get_user_identifier()}"

    def _get_user_identifier(self):
        pass

    def get_token_dict(self) -> dict:
        pass

    def resolve_playlist(self, url_or_identifier: str) -> PlaylistBase:
        pass

    def create_playlist(self) -> PlaylistBase:
        pass


class YoutubeApi(ApiBase):
    type = "youtube"

    def __init__(self, api: pyyoutube.Api, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api = api

    def _get_user_identifier(self):
        return self.api.get_profile().id

    # noinspection PyProtectedMember
    def get_token_dict(self) -> dict:
        return {
            "access_token": self.api._access_token,
            "refresh_token": self.api._refresh_token,
        }

    def resolve_playlist(self, url_or_identifier: str) -> PlaylistBase:
        playlist_resp = self.api.get_playlist_by_id(playlist_id=url_or_identifier)
        if len(playlist_resp.items) != 1:
            raise ValueError("unexpected playlist result")

        return YoutubePlaylist(self.api, playlist_resp.items[0])

    def create_playlist(self) -> PlaylistBase:
        raise NotImplementedError("lol")  # TODO implement via api hack shitfuckery


class SourceMode(enum.IntEnum):
    none = 0
    copy = 1
    move = 2


class TargetMode(enum.IntEnum):
    create = 0
    existing = 1


class TargetDupeMode(enum.IntEnum):
    include = 0
    void = 1
    leave = 2


@dataclass
class Job:
    src_mode: SourceMode
    target_mode: TargetMode
    name: str
    id: str = None
    target: str | None = None
    source: str | None = None
    purge_before_operation: bool = False
    purge_after_limit: SizeAgeLimit = SizeAgeLimit()
    target_dupe_mode: TargetDupeMode = TargetDupeMode.include
    treat_seen_as_dupes: bool = False
    fetch_limit: SizeAgeLimit = SizeAgeLimit()
    reverse_source: bool = False

    # TODO validation logic (illegal configurations)

    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())


@dataclass
class User:
    id: str
    type: str = ""
    jobs: list[Job] = None
    api: ApiBase = None

    def __post_init__(self):
        if self.jobs is None:
            self.jobs = []

    def get_job(self, job_id):
        for job in self.jobs:
            if job.id == job_id:
                return job
        raise KeyError()
