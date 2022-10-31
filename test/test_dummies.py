"""Sanity checks to ensure basic dummy operations work"""
import unittest

from test.dummies import DummyApi, DummyPlaylist, DummyItem


class TestApi(unittest.TestCase):

    def setUp(self):
        self.api = DummyApi()

    def test_creation(self):
        pass  # handles via setUp

    def test_playlist_creation(self):
        playlist = self.api.create_playlist()
        self.assertEqual(len(self.api.playlists), 1)
        self.assertIn(playlist, self.api.playlists.values())

    def test_playlist_lookup(self):
        playlist_id = "foobar123"
        playlist = DummyPlaylist(playlist_id)
        self.api.playlists[playlist_id] = playlist
        self.assertEqual(self.api.resolve_playlist(playlist_id), playlist)

    def test_playlist_loop(self):
        playlist = self.api.create_playlist()
        self.assertEqual(self.api.resolve_playlist(playlist.id), playlist)


class TestPlaylist(unittest.TestCase):

    def setUp(self):
        self.api = DummyApi()
        self.playlist = self.api.create_playlist()

    def test_add_item(self):
        item = DummyItem("some-id")
        self.playlist.add(item)
        self.assertIn(item, self.playlist.items)

    def test_contains_item(self):
        item = DummyItem("some-id")
        self.playlist.items.append(item)
        self.assertTrue(self.playlist.contains(item))

    def test_not_contains_item(self):
        item = DummyItem("some-id")
        self.assertFalse(self.playlist.contains(item))

    def test_delete_at_index(self):
        items = [DummyItem(f"foo-{i}") for i in range(3)]
        self.playlist.items.extend(items)
        self.playlist.remove_at_index(1)
        self.assertEqual(len(self.playlist.items), 2)
        self.assertEqual(self.playlist.items[0], items[0])
        self.assertEqual(self.playlist.items[1], items[2])
        del items[1]
        self.assertCountEqual(self.playlist.items, items)
