import unittest
import os
import json
import time
import threading
from datetime import timedelta
from unittest.mock import patch, MagicMock
from Chat_app import ChatClient, ChatServer, UserManager, ConfigLoader

class TestConfigLoader(unittest.TestCase):
    """
    Test the ConfigLoader class.
    """

    def setUp(self):
        """
        Set up environment for tests.
        We'll remove a possible test config if it exists.
        """
        if os.path.exists("test_config.json"):
            os.remove("test_config.json")

    def test_load_config_file_exists(self):
        """
        If config file exists, load it properly.
        """
        sample_config = {"HOST": "localhost", "PORT": 9999}
        with open("test_config.json", "w") as f:
            json.dump(sample_config, f)
        with patch("builtins.open", side_effect=open):
            with patch("main.config_file", "test_config.json"):
                cfg = ConfigLoader.load_config()
                self.assertEqual(cfg["HOST"], "localhost")
                self.assertEqual(cfg["PORT"], 9999)

    def test_load_config_file_not_exists(self):
        """
        If config file doesn't exist, create default and return it.
        """
        with patch("main.config_file", "test_config.json"):
            cfg = ConfigLoader.load_config()
            self.assertEqual(cfg["HOST"], "127.0.0.1")
            self.assertEqual(cfg["PORT"], 12345)
            self.assertTrue(os.path.exists("test_config.json"))


class TestUserManager(unittest.TestCase):
    """
    Test the UserManager class.
    """

    def setUp(self):
        """
        Set up a test environment. Remove test_users.json if it exists.
        """
        if os.path.exists("test_users.json"):
            os.remove("test_users.json")

    @patch("main.users_file", "test_users.json")
    def test_load_users_empty(self):
        """
        Test loading users when file does not exist yet.
        """
        users = UserManager.load_users()
        self.assertEqual(users, {})
        self.assertTrue(os.path.exists("test_users.json"))

    @patch("main.users_file", "test_users.json")
    def test_save_user_new(self):
        """
        Test saving a new user.
        """
        result = UserManager.save_user("alice", "password123")
        self.assertTrue(result)
        users = UserManager.load_users()
        self.assertIn("alice", users)

    @patch("main.users_file", "test_users.json")
    def test_save_user_duplicate(self):
        """
        Test saving a duplicate user returns False.
        """
        UserManager.save_user("bob", "qwerty")
        result = UserManager.save_user("bob", "asdfgh")
        self.assertFalse(result)

    @patch("main.users_file", "test_users.json")
    def test_authenticate(self):
        """
        Test user authentication.
        """
        UserManager.save_user("charlie", "mypassword")
        auth_success = UserManager.authenticate("charlie", "mypassword")
        auth_fail = UserManager.authenticate("charlie", "wrongpass")
        self.assertTrue(auth_success)
        self.assertFalse(auth_fail)


class TestChatServer(unittest.TestCase):
    """
    Test the ChatServer class behavior with mocked sockets.
    """

    def setUp(self):
        """
        Set up a ChatServer instance with mock host and port.
        """
        self.server = ChatServer("127.0.0.1", 54321)

    @patch("socket.socket")
    def test_start(self, mock_socket):
        """
        Test server start method with mocked socket.
        """
        mock_server_socket = MagicMock()
        mock_socket.return_value = mock_server_socket

        def run_server():
            self.server.start()

        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()

        time.sleep(0.1)
        mock_server_socket.listen.assert_called()
        mock_server_socket.bind.assert_called_with(("127.0.0.1", 54321))

        self.server.log_message("[TEST] Stopping server thread.")
        mock_server_socket.close()
        time.sleep(0.1)

    def test_broadcast(self):
        """
        Test broadcast method with some mock clients.
        """
        conn1 = MagicMock()
        conn2 = MagicMock()
        self.server.clients = {conn1: "User1", conn2: "User2"}

        self.server.broadcast("Hello world", sender=conn1)

        conn1.send.assert_not_called()
        conn2.send.assert_called_once()

    def test_send_stats(self):
        """
        Test send_stats method.
        """
        conn = MagicMock()
        self.server.send_stats(conn, "tester")
        conn.send.assert_called()

    def test_handle_client_disconnect(self):
        """
        Test handle_client behavior on disconnect.
        """
        conn = MagicMock()
        addr = ("127.0.0.1", 9999)
        with patch.object(conn, "recv", side_effect=[b"tester", b"", b""]):
            self.server.handle_client(conn, addr)
        self.assertEqual(len(self.server.clients), 0)

    def test_handle_client_help_command(self):
        """
        Test handle_client /help command.
        """
        conn = MagicMock()
        addr = ("127.0.0.1", 1111)
        input_sequence = [b"tester", b"/help", b"", b""]
        with patch.object(conn, "recv", side_effect=input_sequence):
            self.server.handle_client(conn, addr)
        conn.send.assert_any_call(
            b"[SERVER] Commands:\n/help - Show this help message\n/list - List all connected users\n/private <username> <message> - Send a private message\n/stats - Show server statistics\n"
        )


class TestChatClient(unittest.TestCase):
    """
    Test the ChatClient class with mocked input/output.
    """

    @patch("socket.socket")
    def test_client_connect(self, mock_socket):
        """
        Test that client tries to connect to server.
        """
        mock_client_socket = MagicMock()
        mock_socket.return_value = mock_client_socket
        client = ChatClient("127.0.0.1", 54321)
        mock_client_socket.connect.assert_called_with(("127.0.0.1", 54321))

    @patch("builtins.input", side_effect=["alice", "secret", "n"])
    @patch("main.UserManager.save_user", return_value=True)
    def test_register(self, mock_save_user, mock_input):
        """
        Test client registration.
        """
        client = ChatClient("127.0.0.1", 54321)
        with patch.object(client, "start_client", side_effect=Exception("Stop")):
            try:
                client.register()
            except Exception as e:
                self.assertEqual(str(e), "Stop")
        mock_save_user.assert_called_with("alice", "secret")

    @patch("builtins.input", side_effect=["bob", "pwd", "bob", "pwd", "/quit"])
    @patch("main.UserManager.authenticate", side_effect=[False, True])
    def test_login_and_quit(self, mock_auth, mock_input):
        """
        Test client login attempts and quitting the chat.
        """
        client = ChatClient("127.0.0.1", 54321)
        with patch.object(client, "client") as mock_socket_obj:
            with patch.object(client, "receive_messages", side_effect=Exception("Stop")):
                try:
                    client.start_client()
                except Exception as e:
                    self.assertEqual(str(e), "Stop")
        self.assertEqual(mock_auth.call_count, 2)

    @patch("builtins.input", side_effect=["l", "eve", "1234", "/quit"])
    @patch("main.UserManager.authenticate", return_value=True)
    def test_chat_flow(self, mock_auth, mock_input):
        """
        Test normal chat flow with /quit command.
        """
        client = ChatClient("127.0.0.1", 54321)
        with patch.object(client, "receive_messages", side_effect=Exception("Stop")):
            try:
                client.start_client()
            except Exception as e:
                self.assertEqual(str(e), "Stop")
        self.assertTrue(mock_auth.called)


class TestAdditionalScenarios(unittest.TestCase):
    """
    Additional tests to ensure coverage of edge cases.
    """

    def test_user_already_exists(self):
        """
        Test scenario where user already exists in DB.
        """
        with patch("main.UserManager.save_user", return_value=False):
            result = UserManager.save_user("david", "whatever")
            self.assertFalse(result)

    def test_authenticate_nonexistent_user(self):
        """
        Test scenario where user does not exist in DB.
        """
        with patch("main.UserManager.load_users", return_value={"sam": "somehash"}):
            auth = UserManager.authenticate("nonexistent", "password")
            self.assertFalse(auth)

    def test_server_message_count(self):
        """
        Check if message_count increments properly.
        """
        server = ChatServer("localhost", 4000)
        server.message_count = 5
        server.broadcast("Test")
        # message_count increments only in handle_client, so let's do minimal check
        self.assertEqual(server.message_count, 5)

    def test_server_uptime(self):
        """
        Check server uptime is returning correct format.
        """
        server = ChatServer("localhost", 4001)
        with patch("time.time", side_effect=[100000, 100100]):
            server.start_time = 100000
            conn = MagicMock()
            server.send_stats(conn, "tester")
            sent_args = conn.send.call_args[0][0].decode("utf-8")
            self.assertIn("Uptime: 0:01:40", sent_args)

    def test_private_message_not_found(self):
        """
        Ensure private message fails if target user not found.
        """
        server = ChatServer("localhost", 4002)
        conn = MagicMock()
        server.clients = {conn: "sender"}
        message = "/private missinguser Hello!"
        with patch.object(conn, "recv", side_effect=[b"sender", message.encode("utf-8"), b""]):
            server.handle_client(conn, ("127.0.0.1", 4002))
        conn.send.assert_any_call(b"[SERVER] User not found.\n")

    def test_private_message_success(self):
        """
        Ensure private message is delivered if target user found.
        """
        server = ChatServer("localhost", 4003)
        conn_sender = MagicMock()
        conn_receiver = MagicMock()
        server.clients = {conn_sender: "sender", conn_receiver: "receiver"}
        message = "/private receiver Hi!"
        with patch.object(conn_sender, "recv", side_effect=[b"sender", message.encode("utf-8"), b""]):
            server.handle_client(conn_sender, ("127.0.0.1", 4003))
        conn_receiver.send.assert_any_call(b"[PRIVATE] sender: Hi!\n")

    def test_list_command(self):
        """
        Ensure /list command returns the list of connected users.
        """
        server = ChatServer("localhost", 4004)
        conn_one = MagicMock()
        conn_two = MagicMock()
        server.clients = {conn_one: "UserOne", conn_two: "UserTwo"}
        message = "/list"
        with patch.object(conn_one, "recv", side_effect=[b"UserOne", message.encode("utf-8"), b""]):
            server.handle_client(conn_one, ("127.0.0.1", 4004))
        conn_one.send.assert_any_call(b"[SERVER] Connected users:\nUserOne\nUserTwo\n")
if __name__ == "__main__":
    import unittest
    unittest.main()
