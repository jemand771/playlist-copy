import copy
import uuid

from model import ApiBase, ItemBase, PlaylistBase, SizeAgeLimit


class DummyItem(ItemBase):
    def __init__(self, my_id):
        self.id = my_id
        self.url = f"https://example.com/{my_id}"
        self.artist = "various dummies"
        self.title = f"dummy item with id {my_id} you won't believe what happened next <- GONE WRONG"


class DummyPlaylist(PlaylistBase):
    def __init__(self, my_id):
        self.id = my_id
        self.items = []
        super().__init__()

    def purge(self, limit: SizeAgeLimit):
        self.items.clear()

    def get_items(self, limit: SizeAgeLimit, reverse: bool = False) -> list[DummyItem]:
        return copy.deepcopy(self.items)

    def contains(self, item: DummyItem) -> bool:
        return any(x.id == item.id for x in self.items)

    def add(self, item: DummyItem):
        self.items.append(item)

    def remove_at_index(self, index: int):
        del self.items[index]


class DummyApi(ApiBase):
    type = "dummy"

    def __init__(self):
        self.uid = str(uuid.uuid4())
        self.playlists = {}
        super().__init__()

    def _get_user_identifier(self):
        return self.uid

    def create_playlist(self) -> DummyPlaylist:
        playlist_id = str(uuid.uuid4())
        playlist = DummyPlaylist(playlist_id)
        self.playlists[playlist_id] = playlist
        return playlist

    def resolve_playlist(self, url_or_identifier: str) -> DummyPlaylist:
        return self.playlists[url_or_identifier]
