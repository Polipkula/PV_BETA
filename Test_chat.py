import unittest
from unittest.mock import MagicMock, patch, mock_open
import hashlib
import json
import threading
import time
from datetime import timedelta
from Chat_app import ConfigLoader, UserManager, ChatServer, ChatClient


class TestConfigLoader(unittest.TestCase):
    def setUp(self):
        self.default_config = {"HOST": "127.0.0.1", "PORT": 12345}
        self.custom_config = {"HOST": "192.168.1.1", "PORT": 8080}
        self.invalid_json = "{invalid_json: True,}"

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_load_default_config_creates_file(self, mock_open_fn):
        config = ConfigLoader.load_config()
        self.assertEqual(config, self.default_config)
        mock_open_fn.assert_called_with("config.json", 'w')

    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({"HOST": "192.168.1.1", "PORT": 8080}))
    def test_load_custom_config(self, mock_open_fn):
        config = ConfigLoader.load_config()
        self.assertEqual(config, self.custom_config)
        mock_open_fn.assert_called_with("config.json", 'r')

    @patch("builtins.open", side_effect=PermissionError)
    def test_config_permission_error_read(self, mock_open_fn):
        with self.assertRaises(PermissionError):
            ConfigLoader.load_config()

    @patch("builtins.open", new_callable=mock_open, read_data="{invalid_json: True,}")
    def test_load_config_invalid_json(self, mock_open_fn):
        with self.assertRaises(json.JSONDecodeError):
            ConfigLoader.load_config()

    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({"HOST": "127.0.0.1"}))
    def test_load_config_partial(self, mock_open_fn):
        config = ConfigLoader.load_config()
        expected_config = {"HOST": "127.0.0.1", "PORT": 12345}
        self.assertEqual(config, expected_config)

    def test_config_values_presence(self):
        with patch("Chat_app.ConfigLoader.load_config", return_value=self.default_config):
            config = ConfigLoader.load_config()
            self.assertIn("HOST", config)
            self.assertIn("PORT", config)


class TestUserManager(unittest.TestCase):
    def setUp(self):
        self.mock_users = {"user1": hashlib.sha256("password1".encode()).hexdigest()}
        self.new_user = "new_user"
        self.new_password = "new_password"
        self.duplicate_user = "user1"

    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({"user1": hashlib.sha256("password1".encode()).hexdigest()}))
    def test_load_users_successful(self, mock_open_fn):
        users = UserManager.load_users()
        self.assertEqual(users, self.mock_users)
        mock_open_fn.assert_called_with("users.json", 'r')

    @patch("builtins.open", new_callable=mock_open, read_data="{}")
    def test_load_users_empty(self, mock_open_fn):
        users = UserManager.load_users()
        self.assertEqual(users, {})
        mock_open_fn.assert_called_with("users.json", 'r')

    @patch("builtins.open", new_callable=mock_open, read_data="{invalid_json: True,}")
    def test_load_users_invalid_json(self, mock_open_fn):
        with self.assertRaises(json.JSONDecodeError):
            UserManager.load_users()

    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({"user1": hashlib.sha256("password1".encode()).hexdigest()}))
    def test_authenticate_user_success(self, mock_open_fn):
        auth = UserManager.authenticate("user1", "password1")
        self.assertTrue(auth)

    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({"user1": hashlib.sha256("password1".encode()).hexdigest()}))
    def test_authenticate_user_wrong_password(self, mock_open_fn):
        auth = UserManager.authenticate("user1", "wrong_password")
        self.assertFalse(auth)

    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({"user1": hashlib.sha256("password1".encode()).hexdigest()}))
    def test_authenticate_nonexistent_user(self, mock_open_fn):
        auth = UserManager.authenticate("user2", "password1")
        self.assertFalse(auth)

    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({}))
    def test_authenticate_empty_users(self, mock_open_fn):
        auth = UserManager.authenticate("user1", "password1")
        self.assertFalse(auth)

    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({"user1": "not_a_hash"}))
    def test_authenticate_with_invalid_hash(self, mock_open_fn):
        auth = UserManager.authenticate("user1", "password1")
        self.assertFalse(auth)

    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({}))
    def test_save_user_success(self, mock_open_fn):
        with patch("Chat_app.UserManager.load_users", return_value={}):
            saved = UserManager.save_user(self.new_user, self.new_password)
            self.assertTrue(saved)
            handle = mock_open_fn()
            handle.write.assert_called_once()
            written_data = handle.write.call_args[0][0]
            self.assertIn(self.new_user, json.loads(written_data))

    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({"user1": hashlib.sha256("password1".encode()).hexdigest()}))
    def test_save_duplicate_user(self, mock_open_fn):
        with patch("Chat_app.UserManager.load_users", return_value=self.mock_users):
            saved = UserManager.save_user(self.duplicate_user, "new_password")
            self.assertFalse(saved)
            handle = mock_open_fn()
            handle.write.assert_not_called()

    @patch("builtins.open", new_callable=mock_open)
    def test_save_user_permission_error(self, mock_open_fn):
        mock_open_fn.side_effect = PermissionError
        with patch("Chat_app.UserManager.load_users", return_value={}):
            with self.assertRaises(PermissionError):
                UserManager.save_user(self.new_user, self.new_password)

    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({"user1": hashlib.sha256("password1".encode()).hexdigest()}))
    def test_save_user_empty_username(self, mock_open_fn):
        with patch("Chat_app.UserManager.load_users", return_value=self.mock_users):
            saved = UserManager.save_user("", "password")
            self.assertFalse(saved)

    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({"user1": hashlib.sha256("password1".encode()).hexdigest()}))
    def test_save_user_empty_password(self, mock_open_fn):
        with patch("Chat_app.UserManager.load_users", return_value=self.mock_users):
            saved = UserManager.save_user(self.new_user, "")
            self.assertTrue(saved)
            handle = mock_open_fn()
            written_data = handle.write.call_args[0][0]
            self.assertIn(self.new_user, json.loads(written_data))
            self.assertEqual(json.loads(written_data)[self.new_user], hashlib.sha256("".encode()).hexdigest())


class TestChatServer(unittest.TestCase):
    def setUp(self):
        self.server = ChatServer("127.0.0.1", 12345)
        self.mock_conn = MagicMock()
        self.mock_addr = ("127.0.0.1", 55555)
        self.server.clients = {}
        self.server.message_count = 0
        self.server.start_time = time.time()

    @patch("logging.info")
    def test_log_message(self, mock_logging):
        message = "Test message"
        self.server.log_message(message)
        mock_logging.assert_called_with(message)

    def test_broadcast_no_clients(self):
        self.server.broadcast("Test broadcast")
        # No clients to send, ensure no exceptions

    def test_broadcast_single_client(self):
        mock_client = MagicMock()
        self.server.clients = {mock_client: "test_user"}
        self.server.broadcast("Test broadcast")
        mock_client.send.assert_called_with("Test broadcast".encode("utf-8"))

    def test_broadcast_multiple_clients(self):
        mock_client1 = MagicMock()
        mock_client2 = MagicMock()
        self.server.clients = {mock_client1: "user1", mock_client2: "user2"}
        self.server.broadcast("Broadcast message")
        mock_client1.send.assert_called_with("Broadcast message".encode("utf-8"))
        mock_client2.send.assert_called_with("Broadcast message".encode("utf-8"))

    def test_broadcast_exclude_sender(self):
        mock_client1 = MagicMock()
        mock_client2 = MagicMock()
        self.server.clients = {mock_client1: "user1", mock_client2: "user2"}
        self.server.broadcast("Broadcast message", sender=mock_client1)
        mock_client1.send.assert_not_called()
        mock_client2.send.assert_called_with("Broadcast message".encode("utf-8"))

    @patch.object(ChatServer, 'broadcast')
    def test_handle_client_new_connection(self, mock_broadcast):
        self.mock_conn.recv.return_value = b"user1"
        self.server.handle_client(self.mock_conn, self.mock_addr)
        self.assertIn(self.mock_conn, self.server.clients)
        mock_broadcast.assert_called_with("[SERVER] user1 has joined the chat.", self.mock_conn)

    @patch.object(ChatServer, 'broadcast')
    def test_handle_client_message_handling(self, mock_broadcast):
        self.mock_conn.recv.side_effect = [b"user1", b"Hello, world!", b"/quit"]
        with patch("logging.info"):
            self.server.handle_client(self.mock_conn, self.mock_addr)
            self.assertIn(self.mock_conn, self.server.clients)
            mock_broadcast.assert_any_call("user1: Hello, world!", self.mock_conn)
            self.assertEqual(self.server.message_count, 1)
            self.mock_conn.close.assert_called()

    def test_handle_client_help_command(self):
        self.mock_conn.recv.side_effect = [b"user1", b"/help", b"/quit"]
        with patch.object(self.server, 'broadcast'), \
             patch("logging.info"), \
             patch.object(self.mock_conn, 'send') as mock_send:
            self.server.handle_client(self.mock_conn, self.mock_addr)
            mock_send.assert_called_with(
                "[SERVER] Commands:\n/help - Show this help message\n/list - List all connected users\n/private <username> <message> - Send a private message\n/stats - Show server statistics\n".encode('utf-8')
            )

    def test_handle_client_list_command(self):
        self.server.clients = {self.mock_conn: "user1"}
        self.mock_conn.recv.side_effect = [b"user1", b"/list", b"/quit"]
        with patch.object(self.server, 'broadcast'), \
             patch("logging.info"), \
             patch.object(self.mock_conn, 'send') as mock_send:
            self.server.handle_client(self.mock_conn, self.mock_addr)
            mock_send.assert_called_with("[SERVER] Connected users:\nuser1\n".encode('utf-8'))

    def test_handle_client_private_message_success(self):
        target_conn = MagicMock()
        self.server.clients = {self.mock_conn: "user1", target_conn: "user2"}
        private_message = "/private user2 Hello, user2!"
        self.mock_conn.recv.side_effect = [b"user1", private_message.encode('utf-8'), b"/quit"]
        with patch("logging.info"):
            self.server.handle_client(self.mock_conn, self.mock_addr)
            target_conn.send.assert_called_with("[PRIVATE] user1: Hello, user2!\n".encode('utf-8'))
            self.mock_conn.send.assert_called_with("[PRIVATE] To user2: Hello, user2!\n".encode('utf-8'))

    def test_handle_client_private_message_user_not_found(self):
        self.server.clients = {self.mock_conn: "user1"}
        private_message = "/private user2 Hello, user2!"
        self.mock_conn.recv.side_effect = [b"user1", private_message.encode('utf-8'), b"/quit"]
        with patch.object(self.mock_conn, 'send') as mock_send:
            with patch("logging.info"):
                self.server.handle_client(self.mock_conn, self.mock_addr)
                mock_send.assert_called_with("[SERVER] User not found.\n".encode('utf-8'))

    def test_handle_client_stats_command(self):
        self.server.clients = {self.mock_conn: "user1"}
        self.server.message_count = 10
        self.server.start_time = time.time() - 3600  # 1 hour uptime
        self.mock_conn.recv.side_effect = [b"user1", b"/stats", b"/quit"]
        with patch.object(self.server, 'send_stats') as mock_send_stats:
            with patch("logging.info"):
                self.server.handle_client(self.mock_conn, self.mock_addr)
                mock_send_stats.assert_called_with(self.mock_conn, "user1")

    def test_handle_client_invalid_command(self):
        self.server.clients = {self.mock_conn: "user1"}
        invalid_command = "/invalidcommand"
        self.mock_conn.recv.side_effect = [b"user1", invalid_command.encode('utf-8'), b"/quit"]
        with patch("logging.info"):
            with patch.object(self.server, 'broadcast') as mock_broadcast:
                self.server.handle_client(self.mock_conn, self.mock_addr)
                mock_broadcast.assert_called_with("user1: /invalidcommand", self.mock_conn)
                self.assertEqual(self.server.message_count, 1)

    def test_handle_client_empty_message(self):
        self.mock_conn.recv.side_effect = [b"user1", b"", b"/quit"]
        with patch.object(self.server, 'broadcast') as mock_broadcast:
            self.server.handle_client(self.mock_conn, self.mock_addr)
            mock_broadcast.assert_not_called()

    def test_handle_client_connection_reset(self):
        self.mock_conn.recv.side_effect = [b"user1", ConnectionResetError]
        with patch("logging.info") as mock_logging:
            with patch.object(self.server, 'broadcast') as mock_broadcast:
                self.server.handle_client(self.mock_conn, self.mock_addr)
                mock_logging.assert_called_with(f"[DISCONNECTED] {self.mock_addr} forcibly closed the connection.")
                self.assertNotIn(self.mock_conn, self.server.clients)

    def test_handle_client_unexpected_exception(self):
        self.mock_conn.recv.side_effect = [b"user1", Exception("Unexpected error")]
        with patch("logging.info") as mock_logging:
            with patch.object(self.server, 'broadcast') as mock_broadcast:
                self.server.handle_client(self.mock_conn, self.mock_addr)
                mock_logging.assert_called_with("[ERROR] ('127.0.0.1', 55555): Unexpected error")
                self.assertNotIn(self.mock_conn, self.server.clients)

    def test_send_stats(self):
        username = "user1"
        conn = MagicMock()
        self.server.clients = {conn: username}
        self.server.message_count = 5
        self.server.start_time = time.time() - 120  # 2 minutes uptime
        with patch("time.time", return_value=self.server.start_time + 120):
            self.server.send_stats(conn, username)
            expected_uptime = str(timedelta(seconds=120))
            expected_message = (
                f"[SERVER STATS]\n"
                f"Active users: {len(self.server.clients)}\n"
                f"Total messages: {self.server.message_count}\n"
                f"Uptime: {expected_uptime}"
            )
            conn.send.assert_called_with(expected_message.encode('utf-8'))

    @patch.object(ChatServer, 'broadcast')
    def test_handle_client_message_count_increment(self, mock_broadcast):
        self.mock_conn.recv.side_effect = [b"user1", b"Test message", b"/quit"]
        with patch("logging.info"):
            self.server.handle_client(self.mock_conn, self.mock_addr)
            self.assertEqual(self.server.message_count, 1)

    @patch.object(ChatServer, 'broadcast')
    def test_handle_client_multiple_messages(self, mock_broadcast):
        self.mock_conn.recv.side_effect = [b"user1", b"Message 1", b"Message 2", b"/quit"]
        with patch("logging.info"):
            self.server.handle_client(self.mock_conn, self.mock_addr)
            self.assertEqual(self.server.message_count, 2)
            calls = [
                unittest.mock.call("user1: Message 1", self.mock_conn),
                unittest.mock.call("user1: Message 2", self.mock_conn)
            ]
            mock_broadcast.assert_has_calls(calls, any_order=False)

    @patch.object(ChatServer, 'broadcast')
    def test_broadcast_with_exceptions(self, mock_broadcast):
        mock_client = MagicMock()
        self.server.clients = {mock_client: "user2"}
        self.server.broadcast = MagicMock(side_effect=Exception("Broadcast failed"))
        with patch("logging.info") as mock_logging:
            self.server.broadcast("Test message")
            mock_client.send.assert_called_with("Test message".encode('utf-8'))
            mock_logging.assert_called_with("[ERROR] Sending message: Broadcast failed")


class TestChatClient(unittest.TestCase):
    def setUp(self):
        self.mock_socket = MagicMock()
        self.patcher = patch("socket.socket", return_value=self.mock_socket)
        self.mock_socket_class = self.patcher.start()
        self.client = ChatClient("127.0.0.1", 12345)

    def tearDown(self):
        self.patcher.stop()

    @patch("builtins.input", side_effect=["new_user", "new_password"])
    @patch("Chat_app.UserManager.save_user", return_value=True)
    @patch("Chat_app.ChatClient.start_client")
    def test_register_successful(self, mock_start_client, mock_save_user, mock_input):
        self.client.register()
        mock_save_user.assert_called_with("new_user", "new_password")
        mock_start_client.assert_called()

    @patch("builtins.input", side_effect=["existing_user", "password"])
    @patch("Chat_app.UserManager.save_user", return_value=False)
    def test_register_duplicate_user(self, mock_save_user, mock_input):
        with patch("builtins.print") as mock_print:
            self.client.register()
            mock_save_user.assert_called_with("existing_user", "password")
            mock_print.assert_called_with("Username already exists! Try again.")

    @patch("builtins.input", side_effect=["", "password"])
    @patch("Chat_app.UserManager.save_user", return_value=True)
    def test_register_empty_username(self, mock_save_user, mock_input):
        with patch("builtins.print") as mock_print:
            self.client.register()
            mock_save_user.assert_called_with("", "password")
            mock_print.assert_called_with("Registration successful! You can now log in.")

    @patch("builtins.input", side_effect=["user", ""])
    @patch("Chat_app.UserManager.save_user", return_value=True)
    def test_register_empty_password(self, mock_save_user, mock_input):
        with patch("builtins.print") as mock_print:
            self.client.register()
            mock_save_user.assert_called_with("user", "")
            mock_print.assert_called_with("Registration successful! You can now log in.")

    @patch("builtins.input", side_effect=["user1", "password1"])
    @patch("Chat_app.UserManager.save_user", side_effect=PermissionError)
    def test_register_permission_error(self, mock_save_user, mock_input):
        with self.assertRaises(PermissionError):
            self.client.register()

    @patch("builtins.input", side_effect=["user1", "password1"])
    @patch("Chat_app.UserManager.authenticate", return_value=True)
    @patch("Chat_app.ChatClient.chat")
    def test_login_successful(self, mock_chat, mock_authenticate, mock_input):
        self.client.login()
        mock_authenticate.assert_called_with("user1", "password1")
        self.assertEqual(self.client.username, "user1")
        self.mock_socket.send.assert_called_with("user1".encode('utf-8'))
        mock_chat.assert_called()

    @patch("builtins.input", side_effect=["user1", "wrong_password", "user1", "password1"])
    @patch("Chat_app.UserManager.authenticate", side_effect=[False, True])
    @patch("Chat_app.ChatClient.chat")
    def test_login_retry_successful(self, mock_chat, mock_authenticate, mock_input):
        self.client.login()
        self.assertEqual(mock_authenticate.call_count, 2)
        self.assertEqual(self.client.username, "user1")
        self.mock_socket.send.assert_called_with("user1".encode('utf-8'))
        mock_chat.assert_called()

    @patch("builtins.input", side_effect=["user1", "password1", "Hello, world!", "/quit"])
    @patch("Chat_app.UserManager.authenticate", return_value=True)
    def test_full_client_flow(self, mock_authenticate, mock_input):
        with patch.object(self.client, "receive_messages") as mock_receive:
            with patch.object(self.client.client, "send") as mock_send:
                self.client.start_client()
                mock_authenticate.assert_called_with("user1", "password1")
                mock_send.assert_any_call("user1".encode('utf-8'))
                self.client.chat()
                mock_send.assert_any_call("Hello, world!".encode('utf-8'))
                mock_send.assert_any_call("/quit".encode('utf-8'))
                self.mock_socket.close.assert_called()

    @patch("builtins.input", side_effect=["Hello, world!", "/quit"])
    def test_chat_send_quit(self, mock_input):
        with patch("builtins.print") as mock_print:
            with patch.object(self.client.client, "send") as mock_send:
                self.client.chat()
                mock_send.assert_called_with("/quit".encode('utf-8'))
                mock_print.assert_called_with("You have left the chat.")
                self.mock_socket.close.assert_called()

    @patch("builtins.input", side_effect=["Hello, world!", "/quit"])
    def test_chat_send_message_and_quit(self, mock_input):
        with patch("builtins.print") as mock_print:
            with patch.object(self.client.client, "send") as mock_send:
                self.client.chat()
                mock_send.assert_any_call("Hello, world!".encode('utf-8'))
                mock_send.assert_any_call("/quit".encode('utf-8'))
                self.mock_socket.close.assert_called()

    @patch("builtins.input", side_effect=["user1", "password1", "Hello", "/quit"])
    @patch("Chat_app.UserManager.authenticate", return_value=True)
    def test_login_and_chat_flow(self, mock_authenticate, mock_input):
        with patch.object(self.client, "receive_messages") as mock_receive:
            with patch.object(self.client.client, "send") as mock_send:
                self.client.start_client()
                self.client.login()
                mock_authenticate.assert_called_with("user1", "password1")
                self.assertEqual(self.client.username, "user1")
                mock_send.assert_called_with("user1".encode('utf-8'))
                self.client.chat()
                mock_send.assert_any_call("Hello".encode('utf-8'))
                mock_send.assert_any_call("/quit".encode('utf-8'))
                self.mock_socket.close.assert_called()

    @patch("builtins.input", side_effect=["user1", "password1", "/quit"])
    @patch("Chat_app.UserManager.authenticate", return_value=True)
    def test_chat_start_and_quit_immediately(self, mock_authenticate, mock_input):
        with patch.object(self.client, "receive_messages") as mock_receive:
            with patch.object(self.client.client, "send") as mock_send:
                self.client.start_client()
                self.client.chat()
                mock_send.assert_any_call("/quit".encode('utf-8'))
                self.mock_socket.close.assert_called()

    @patch("builtins.input", side_effect=["user1", "password1", "Hello!", "/quit"])
    @patch("Chat_app.UserManager.authenticate", return_value=True)
    def test_client_chat_sequence(self, mock_authenticate, mock_input):
        with patch.object(self.client, "receive_messages") as mock_receive:
            with patch.object(self.client.client, "send") as mock_send:
                self.client.start_client()
                self.client.chat()
                expected_calls = [
                    unittest.mock.call("Hello!".encode('utf-8')),
                    unittest.mock.call("/quit".encode('utf-8'))
                ]
                mock_send.assert_has_calls(expected_calls, any_order=False)
                self.mock_socket.close.assert_called()

    @patch("builtins.input", side_effect=["user1", "password1", "Hello!", "/quit"])
    @patch("Chat_app.UserManager.authenticate", return_value=True)
    def test_client_send_and_receive_messages(self, mock_authenticate, mock_input):
        self.client.client.recv.side_effect = [b"Hello from server", b"/quit"]
        with patch("builtins.print") as mock_print:
            with patch.object(threading.Thread, "start") as mock_thread_start:
                self.client.chat()
                self.client.receive_messages()
                mock_print.assert_any_call("\rHello from server\nuser: ", end="")


class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.server = ChatServer("127.0.0.1", 12345)
        self.client1 = ChatClient("127.0.0.1", 12345)
        self.client2 = ChatClient("127.0.0.1", 12345)

    @patch.object(ChatServer, "broadcast")
    def test_broadcast_integration(self, mock_broadcast):
        mock_client1 = MagicMock()
        mock_client2 = MagicMock()
        self.server.clients = {mock_client1: "user1", mock_client2: "user2"}
        self.server.broadcast("Integration Test Message")
        mock_client1.send.assert_called_with("Integration Test Message".encode('utf-8'))
        mock_client2.send.assert_called_with("Integration Test Message".encode('utf-8'))

    @patch.object(ChatServer, "broadcast")
    def test_private_message_between_clients(self, mock_broadcast):
        mock_client1_conn = MagicMock()
        mock_client2_conn = MagicMock()
        self.server.clients = {mock_client1_conn: "user1", mock_client2_conn: "user2"}

        private_message = "/private user2 Hello, user2!"
        self.server.handle_client = MagicMock()

        with patch.object(self.server, 'handle_client') as mock_handle_client:
            self.server.handle_client(mock_client1_conn, ("127.0.0.1", 55551))
            mock_client1_conn.recv.side_effect = [private_message.encode('utf-8')]
            self.server.handle_client(mock_client1_conn, ("127.0.0.1", 55551))
            mock_client2_conn.send.assert_called_with("[PRIVATE] user1: Hello, user2!\n".encode('utf-8'))
            mock_client1_conn.send.assert_called_with("[PRIVATE] To user2: Hello, user2!\n".encode('utf-8'))

    @patch.object(ChatServer, "send_stats")
    def test_stats_integration(self, mock_send_stats):
        mock_conn = MagicMock()
        self.server.clients = {mock_conn: "user1"}
        self.server.message_count = 20
        self.server.start_time = time.time() - 600  # 10 minutes uptime

        stats_command = b"/stats"
        self.server.handle_client(mock_conn, ("127.0.0.1", 55555))
        mock_send_stats.assert_called_with(mock_conn, "user1")

    @patch.object(ChatServer, "broadcast")
    def test_user_join_leave_integration(self, mock_broadcast):
        mock_conn = MagicMock()
        # Simulate user joining
        self.server.handle_client(mock_conn, ("127.0.0.1", 55555))
        self.server.clients[mock_conn] = "user1"
        mock_broadcast.assert_called_with("[SERVER] user1 has joined the chat.", mock_conn)
        # Simulate user leaving
        self.server.handle_client(mock_conn, ("127.0.0.1", 55555))
        del self.server.clients[mock_conn]
        mock_broadcast.assert_called_with("[SERVER] user1 has left the chat.", mock_conn)

    @patch.object(ChatServer, "broadcast")
    def test_multiple_private_messages_integration(self, mock_broadcast):
        mock_client1 = MagicMock()
        mock_client2 = MagicMock()
        mock_client3 = MagicMock()
        self.server.clients = {mock_client1: "user1", mock_client2: "user2", mock_client3: "user3"}

        # user1 sends private message to user2
        private_message1 = "/private user2 Hi user2!"
        self.server.handle_client(mock_client1, ("127.0.0.1", 55551))
        mock_client1.recv.side_effect = [private_message1.encode('utf-8')]
        self.server.handle_client(mock_client1, ("127.0.0.1", 55551))
        mock_client2.send.assert_called_with("[PRIVATE] user1: Hi user2!\n".encode('utf-8'))
        mock_client1.send.assert_called_with("[PRIVATE] To user2: Hi user2!\n".encode('utf-8'))

        # user2 sends private message to user3
        private_message2 = "/private user3 Hello user3!"
        self.server.handle_client(mock_client2, ("127.0.0.1", 55552))
        mock_client2.recv.side_effect = [private_message2.encode('utf-8')]
        self.server.handle_client(mock_client2, ("127.0.0.1", 55552))
        mock_client3.send.assert_called_with("[PRIVATE] user2: Hello user3!\n".encode('utf-8'))
        mock_client2.send.assert_called_with("[PRIVATE] To user3: Hello user3!\n".encode('utf-8'))


if __name__ == "__main__":
    unittest.main(verbosity=2)
