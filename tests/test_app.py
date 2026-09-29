import unittest

import app as game_app


class PublishedAppTests(unittest.TestCase):
    def setUp(self):
        game_app.games.clear()
        self.first = game_app.socketio.test_client(game_app.app)
        self.second = game_app.socketio.test_client(game_app.app)

    def tearDown(self):
        self.first.disconnect()
        self.second.disconnect()
        game_app.games.clear()

    def test_health_and_home_routes(self):
        client = game_app.app.test_client()
        self.assertEqual(client.get("/healthz").json, {"status": "ok"})
        self.assertEqual(client.get("/").status_code, 200)

    def test_room_game_and_rematch(self):
        self.first.emit("join_game", {"name": "Alice"})
        first_events = self.first.get_received()
        first_join = next(event for event in first_events if event["name"] == "joined_game")
        room_id = first_join["args"][0]["room_id"]
        first_sid = first_join["args"][0]["player_id"]

        self.second.emit("join_game", {"name": "Bob", "room_id": room_id})
        second_events = self.second.get_received()
        second_join = next(event for event in second_events if event["name"] == "joined_game")
        second_sid = second_join["args"][0]["player_id"]
        game = game_app.games[room_id]

        chooser = self.first if game["chooser"] == first_sid else self.second
        guesser = self.first if game["guesser"] == first_sid else self.second
        chooser.emit("submit_word", {"room_id": room_id, "word": "chat"})
        self.assertEqual(game["state"], "playing")

        for letter in "chat":
            guesser.emit("guess_letter", {"room_id": room_id, "letter": letter})

        self.assertEqual(game["state"], "finished")
        self.assertEqual(game["players"][game["guesser"]]["score"], 1)

        previous_guesser = game["guesser"]
        self.first.emit("play_again", {"room_id": room_id})
        self.second.emit("play_again", {"room_id": room_id})
        self.assertEqual(game["state"], "choosing")
        self.assertEqual(game["chooser"], previous_guesser)


if __name__ == "__main__":
    unittest.main()
