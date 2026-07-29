"""按钮交互 / ephemeral 的构造与序列化层单测（不访问真实服务端）。

运行：python -m unittest discover -s tests（在 python/ 目录下）。
"""

import unittest
from unittest.mock import patch

from newtspeak_bot import Interaction, OwlBotClient

SAMPLE_PAYLOAD = {
    "id": "1234567890123456789",
    "token": "newtint_abc",
    "guild_id": "guild-uuid",
    "channel_id": "channel-uuid",
    "message_id": "9876543210",
    "custom_id": "approve:42",
    "member": {"user_id": "user-uuid", "username": "alice", "roles": ["role-a"]},
    "expires_at": "2026-07-26T12:15:00Z",
}


class InteractionTest(unittest.TestCase):
    def setUp(self):
        self.client = OwlBotClient("https://newt.example.com", "newtbot_test")

    def test_fields(self):
        interaction = Interaction(self.client, SAMPLE_PAYLOAD)
        self.assertEqual(interaction.id, "1234567890123456789")
        self.assertEqual(interaction.token, "newtint_abc")
        self.assertEqual(interaction.custom_id, "approve:42")
        self.assertEqual(interaction.message_id, "9876543210")
        self.assertEqual(interaction.member["user_id"], "user-uuid")
        self.assertEqual(interaction.expires_at, "2026-07-26T12:15:00Z")

    def test_ack_reply_update(self):
        interaction = Interaction(self.client, SAMPLE_PAYLOAD)
        with patch.object(OwlBotClient, "_request", return_value={"id": "m1"}) as mock:
            interaction.ack()
            method, path, body = mock.call_args.args
            self.assertEqual(method, "POST")
            self.assertEqual(path, "/interactions/1234567890123456789/callback")
            self.assertEqual(body, {"type": "ack", "token": "newtint_abc"})

            interaction.reply("已处理", card={"title": "OK"})
            _, _, body = mock.call_args.args
            self.assertEqual(body["type"], "reply")
            self.assertTrue(body["ephemeral"])  # 缺省 ephemeral=True
            self.assertEqual(body["content"], "已处理")
            self.assertEqual(body["card"], {"title": "OK"})

            interaction.reply("公开", ephemeral=False)
            _, _, body = mock.call_args.args
            self.assertFalse(body["ephemeral"])

            interaction.update_message(card={"title": "已通过"})
            _, _, body = mock.call_args.args
            self.assertEqual(body["type"], "update_message")
            self.assertNotIn("content", body)


class EphemeralTest(unittest.TestCase):
    def test_send_ephemeral_body(self):
        client = OwlBotClient("https://newt.example.com", "newtbot_test")
        with patch.object(OwlBotClient, "_request", return_value={"id": "m1"}) as mock:
            client.send_ephemeral("channel-uuid", "user-uuid", "仅你可见")
            _, path, body = mock.call_args.args
            self.assertEqual(path, "/channels/channel-uuid/messages")
            self.assertEqual(body["visible_to_user_ids"], ["user-uuid"])

    def test_send_message_omits_field_by_default(self):
        client = OwlBotClient("https://newt.example.com", "newtbot_test")
        with patch.object(OwlBotClient, "_request", return_value={"id": "m1"}) as mock:
            client.send_message("channel-uuid", "hi")
            _, _, body = mock.call_args.args
            self.assertNotIn("visible_to_user_ids", body)  # 兼容旧服务端


if __name__ == "__main__":
    unittest.main()
