import enum
import uuid
from dataclasses import dataclass

import pyyoutube


class Item:
    pass


class Playlist:

    def get_elements(self) -> list[Item]:
        pass

    def append(self, item: Item):
        pass


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


@dataclass(eq=True, frozen=True)
class SizeAgeLimit:
    count: int | None = None
    age_seconds: int | None = None


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
