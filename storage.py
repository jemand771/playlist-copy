import dataclasses
import json
import os

import redis

from model import Job, User, YoutubeApi
from util import make_youtube_api


class Storage:

    def __init__(self):
        self.redis = redis.Redis(
            **{
                key: value for key, value in dict(
                    hostname=os.environ.get("REDIS_HOST"),
                    port=os.environ.get("REDIS_PORT")
                ).items()
                if value is not None
            }
        )

    def get_user(self, uid: str) -> User:
        user_dict = json.loads(self.redis.get(uid))

        if user_dict.get("type") == "youtube":
            _api = make_youtube_api()
            _api._access_token = user_dict["token"]["access_token"]
            _api._refresh_token = user_dict["token"]["refresh_token"]
            user_dict["api"] = YoutubeApi(_api)
        else:
            # TODO handle no suitable api type
            raise Exception("huh")

        del user_dict["token"]
        user = User(**user_dict)
        user.jobs = [Job(**job_dict) for job_dict in user_dict["jobs"]]
        return user

    def user_exists(self, uid: str):
        return self.redis.exists(uid)

    def update_user(self, user: User):
        db_dict = dataclasses.asdict(user)
        db_dict["token"] = user.api.get_token_dict()
        del db_dict["api"]
        self.redis.set(user.id, json.dumps(db_dict, ensure_ascii=False))
