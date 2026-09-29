import unittest
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import app as game_app
from db import Database


class PublishedAppTests(unittest.TestCase):
    def setUp(self):
        self.original_database = game_app.database
        self.database_dir = tempfile.TemporaryDirectory()
        game_app.database = Database(Path(self.database_dir.name) / "test.sqlite3")
        game_app.database.init()
        game_app.games.clear()
        self.first = game_app.socketio.test_client(game_app.app)
        self.second = game_app.socketio.test_client(game_app.app)

    def tearDown(self):
        self.first.disconnect()
        self.second.disconnect()
        game_app.games.clear()
        game_app.database = self.original_database
        self.database_dir.cleanup()

    def test_health_and_home_routes(self):
        client = game_app.app.test_client()
        self.assertEqual(client.get("/healthz").json, {"status": "ok"})
        self.assertEqual(client.get("/").status_code, 200)
        self.assertEqual(
            client.get("/static/vendor/socket.io.min.js").status_code,
            200,
        )

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

    def test_multiplayer_keeps_accented_ligature_as_one_letter_position(self):
        self.first.emit("join_game", {"name": "Alice"})
        first_join = next(
            event for event in self.first.get_received() if event["name"] == "joined_game"
        )
        room_id = first_join["args"][0]["room_id"]
        first_sid = first_join["args"][0]["player_id"]
        self.second.emit("join_game", {"name": "Bob", "room_id": room_id})
        second_join = next(
            event for event in self.second.get_received() if event["name"] == "joined_game"
        )
        second_sid = second_join["args"][0]["player_id"]
        game = game_app.games[room_id]

        chooser = self.first if game["chooser"] == first_sid else self.second
        guesser = self.first if game["guesser"] == first_sid else self.second
        chooser.emit("submit_word", {"room_id": room_id, "word": "cœur"})
        for letter in "cour":
            guesser.emit("guess_letter", {"room_id": room_id, "letter": letter})

        events = guesser.get_received()
        finished = next(event["args"][0] for event in events if event["name"] == "game_over")
        self.assertEqual(finished["word"], "cœur")
        self.assertEqual(game["state"], "finished")

    def test_room_chat_is_broadcast_to_both_players(self):
        self.first.emit("join_game", {"name": "Alice"})
        first_join = next(
            event for event in self.first.get_received() if event["name"] == "joined_game"
        )
        room_id = first_join["args"][0]["room_id"]
        self.second.emit("join_game", {"name": "Bob", "room_id": room_id})
        self.second.get_received()

        self.first.emit(
            "chat_message",
            {"room_id": room_id, "message": "  Bonne   chance !  "},
        )
        first_chat = next(
            event for event in self.first.get_received() if event["name"] == "chat_message"
        )
        second_chat = next(
            event for event in self.second.get_received() if event["name"] == "chat_message"
        )
        self.assertEqual(first_chat["args"][0]["message"], "Bonne chance !")
        self.assertEqual(first_chat["args"][0], second_chat["args"][0])

    def test_multiplayer_joker_reveals_a_letter_and_costs_points(self):
        client = game_app.app.test_client()
        token = client.post("/api/profile", json={"nickname": "Joker"}).json["token"]
        with patch("app.secrets.choice", side_effect=lambda values: values[0]):
            self.first.emit("join_game", {"name": "Alice"})
            first_join = next(
                event for event in self.first.get_received() if event["name"] == "joined_game"
            )
            room_id = first_join["args"][0]["room_id"]
            first_sid = first_join["args"][0]["player_id"]
            self.second.emit("join_game", {"name": "Joker", "token": token, "room_id": room_id})
            second_join = next(
                event for event in self.second.get_received() if event["name"] == "joined_game"
            )
            second_sid = second_join["args"][0]["player_id"]
            game = game_app.games[room_id]
            self.assertEqual(game["chooser"], first_sid)
            self.assertEqual(game["guesser"], second_sid)

            self.first.emit("submit_word", {"room_id": room_id, "word": "chat"})
            self.second.emit("use_hint", {"room_id": room_id})
            self.assertEqual(game["hints_used"], 1)
            for letter in "chat":
                if letter not in game["guessed_letters"]:
                    self.second.emit("guess_letter", {"room_id": room_id, "letter": letter})

            second_events = self.second.get_received()
            result = next(
                event["args"][0]
                for event in second_events
                if event["name"] == "profile_updated"
            )
            self.assertEqual(result["match"]["hint_penalty"], 30)
            self.assertEqual(result["profile"]["current_streak"], 0)


class NewGameModeTests(unittest.TestCase):
    def setUp(self):
        self.original_database = game_app.database
        self.database_dir = tempfile.TemporaryDirectory()
        game_app.database = Database(Path(self.database_dir.name) / "test.sqlite3")
        game_app.database.init()
        game_app.games.clear()
        game_app.bot_games.clear()
        self.http = game_app.app.test_client()
        self.socket = game_app.socketio.test_client(game_app.app)
        response = self.http.post("/api/profile", json={"nickname": "BotTest"})
        self.assertEqual(response.status_code, 201)
        self.token = response.json["token"]

    def tearDown(self):
        self.socket.disconnect()
        game_app.games.clear()
        game_app.bot_games.clear()
        game_app.database = self.original_database
        self.database_dir.cleanup()

    def test_profile_and_game_data_api(self):
        restored = self.http.post(
            "/api/profile", json={"token": self.token}
        )
        self.assertEqual(restored.status_code, 200)
        self.assertEqual(restored.json["profile"]["nickname"], "BotTest")
        self.assertEqual(len(self.http.get("/api/game-data").json["bots"]), 5)
        self.assertEqual(
            self.http.get("/api/leaderboard").status_code,
            200,
        )

    def test_same_profile_can_rejoin_a_full_room_after_socket_reconnect(self):
        opponent = game_app.socketio.test_client(game_app.app)
        replacement = game_app.socketio.test_client(game_app.app)
        try:
            self.socket.emit("join_game", {"token": self.token, "name": "BotTest"})
            joined = next(
                event for event in self.socket.get_received() if event["name"] == "joined_game"
            )
            room_id = joined["args"][0]["room_id"]
            old_sid = joined["args"][0]["player_id"]
            opponent.emit("join_game", {"name": "Ami", "room_id": room_id})
            opponent.get_received()

            replacement.emit(
                "join_game", {"token": self.token, "name": "BotTest", "room_id": room_id}
            )
            events = replacement.get_received()
            resumed = next(event for event in events if event["name"] == "joined_game")
            new_sid = resumed["args"][0]["player_id"]
            game = game_app.games[room_id]
            self.assertNotEqual(new_sid, old_sid)
            self.assertNotIn(old_sid, game["players"])
            self.assertEqual(len(game["players"]), 2)
            self.assertEqual(game["players"][new_sid]["token"], self.token)
            self.assertIn(game["state"], {"choosing", "playing"})
        finally:
            replacement.disconnect()
            opponent.disconnect()

    def test_solo_bot_never_sends_secret_before_game_over(self):
        self.socket.emit(
            "start_bot_game",
            {"token": self.token, "bot_id": "beginner", "mode": "guess"},
        )
        events = self.socket.get_received()
        started = next(event["args"][0] for event in events if event["name"] == "bot_game_started")
        self.assertNotIn("word", started)
        self.assertNotIn("secret", started)
        self.assertTrue(set(started["masked"].replace(" ", "")) <= {"_"})

        sid = next(iter(game_app.bot_games))
        first_secret = game_app.bot_games[sid]["entry"]["word"]
        secret_keys = game_app.bot_games[sid]["word_keys"]
        letters = dict.fromkeys(letter for key in secret_keys for letter in key)
        for letter in letters:
            self.socket.emit("bot_guess_letter", {"letter": letter})
        events = self.socket.get_received()
        ended = next(event["args"][0] for event in events if event["name"] == "bot_game_over")
        self.assertTrue(ended["won"])
        self.assertEqual(ended["word"], first_secret)
        self.assertEqual(ended["profile"]["matches"], 1)
        self.assertNotIn(sid, game_app.bot_games)

        self.socket.emit(
            "start_bot_game",
            {"token": self.token, "bot_id": "beginner", "mode": "guess"},
        )
        next_round = next(
            event
            for event in self.socket.get_received()
            if event["name"] == "bot_game_started"
        )
        self.assertNotIn("word", next_round["args"][0])
        self.assertNotEqual(
            next(iter(game_app.bot_games.values()))["entry"]["word"],
            first_secret,
        )

    def test_duel_submits_hidden_word_then_bot_takes_a_real_turn(self):
        self.socket.emit(
            "start_bot_game",
            {"token": self.token, "bot_id": "beginner", "mode": "duel"},
        )
        start_events = self.socket.get_received()
        self.assertTrue(any(event["name"] == "bot_word_required" for event in start_events))
        started = next(
            event["args"][0]
            for event in start_events
            if event["name"] == "bot_game_started"
        )
        self.assertNotIn("word", started)

        self.socket.emit("submit_bot_word", {"word": "chat"})
        self.assertTrue(
            any(
                event["name"] == "bot_duel_started"
                for event in self.socket.get_received()
            )
        )
        with patch("app.bot_delay", return_value=0):
            self.socket.emit("bot_duel_guess", {"letter": "z"})
            deadline = time.time() + 2
            while time.time() < deadline:
                if not game_app.bot_games[next(iter(game_app.bot_games))]["bot_turn_pending"]:
                    break
                time.sleep(0.01)
            turn_events = self.socket.get_received()
        update = next(
            event["args"][0]
            for event in turn_events
            if event["name"] == "bot_duel_update"
        )
        self.assertIn("letter", update)

    def test_twenty_boss_rounds_never_repeat_and_each_tenth_is_a_trap(self):
        seen = set()
        for duel_number in range(1, 21):
            self.socket.emit(
                "start_bot_game",
                {"token": self.token, "bot_id": "boss", "mode": "guess"},
            )
            self.socket.get_received()
            sid = next(iter(game_app.bot_games))
            game = game_app.bot_games[sid]
            word = game["entry"]
            self.assertNotIn(word["normalized"], seen)
            seen.add(word["normalized"])
            if duel_number % 10 == 0:
                self.assertTrue(word["trap"])

            letters = dict.fromkeys(
                letter for key in game["word_keys"] for letter in key
            )
            for letter in letters:
                self.socket.emit("bot_guess_letter", {"letter": letter})
            ended = [
                event
                for event in self.socket.get_received()
                if event["name"] == "bot_game_over"
            ]
            self.assertEqual(len(ended), 1)

        self.assertEqual(len(seen), 20)


if __name__ == "__main__":
    unittest.main()
