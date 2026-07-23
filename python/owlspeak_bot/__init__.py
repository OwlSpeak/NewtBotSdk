"""OwlSpeak Bot SDK（Python）。

REST 部分仅依赖标准库；Gateway 实时事件需可选依赖 ``websockets``
（``pip install owlspeak-bot[gateway]``）。

认证：``Authorization: Bot <token>``；基础地址自动拼接 ``/bot-api/v1``。
"""

from __future__ import annotations

import asyncio
import json
import uuid
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, AsyncIterator, Callable, Dict, Iterable, List, Optional

__all__ = ["OwlBotClient", "OwlBotError", "MessageStream", "run_gateway"]


class OwlBotError(Exception):
    """SDK 统一错误：携带 HTTP 状态码与服务端错误码。"""

    def __init__(self, status: int, code: Optional[str], message: Optional[str]):
        super().__init__(message or code or f"请求失败（{status}）")
        self.status = status
        self.code = code


class MessageStream:
    """流式消息句柄：append 追加分片、end 收束（可带终态卡片）。"""

    def __init__(self, client: "OwlBotClient", channel_id: str, message: Dict[str, Any]):
        self._client = client
        self.channel_id = channel_id
        self.message = message
        self.id = str(message["id"])
        self.ended = False

    def append(self, delta: str) -> Dict[str, Any]:
        if self.ended:
            raise RuntimeError("流式消息已结束")
        return self._client._request(
            "POST", f"/channels/{self.channel_id}/messages/{self.id}/stream", {"delta": delta}
        )

    def end(self, content: Optional[str] = None, card: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self.ended:
            return self.message
        self.ended = True
        body: Dict[str, Any] = {}
        if content is not None:
            body["content"] = content
        if card is not None:
            body["card"] = card
        self.message = self._client._request(
            "POST", f"/channels/{self.channel_id}/messages/{self.id}/stream/end", body
        )
        return self.message

    def __enter__(self) -> "MessageStream":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if not self.ended:
            self.end()


class OwlBotClient:
    """OwlSpeak 机器人开放 API 客户端（同步 REST）。"""

    def __init__(self, base_url: str, token: str, timeout: float = 15.0):
        if not base_url or not token:
            raise ValueError("base_url 与 token 必填")
        self.api_base = base_url.rstrip("/") + "/bot-api/v1"
        self.token = token
        self.timeout = timeout

    # ---------- 内部请求 ----------

    def _request(self, method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Any:
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(self.api_base + path, data=data, method=method)
        request.add_header("Authorization", f"Bot {self.token}")
        if data is not None:
            request.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                if response.status == 204:
                    return None
                return json.loads(response.read() or b"{}")
        except urllib.error.HTTPError as exc:
            try:
                payload = json.loads(exc.read() or b"{}")
            except Exception:
                payload = {}
            error = payload.get("error") or {}
            raise OwlBotError(exc.code, error.get("code"), error.get("message")) from None

    # ---------- 基础资源 ----------

    def me(self) -> Dict[str, Any]:
        return self._request("GET", "/me")

    def guilds(self) -> List[Dict[str, Any]]:
        return self._request("GET", "/guilds").get("guilds", [])

    def channels(self, guild_id: str) -> List[Dict[str, Any]]:
        return self._request("GET", f"/guilds/{guild_id}/channels").get("channels", [])

    def members(self, guild_id: str) -> List[Dict[str, Any]]:
        """成员目录（含 is_bot、is_owner、role_ids）。"""
        return self._request("GET", f"/guilds/{guild_id}/members").get("members", [])

    def member(self, guild_id: str, member_id: str) -> Dict[str, Any]:
        """单成员详情；member_id 可为 members.id 或 user_id。"""
        return self._request("GET", f"/guilds/{guild_id}/members/{member_id}")

    def permissions(self, guild_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/guilds/{guild_id}/permissions/@me")

    def channel_permissions(self, guild_id: str, channel_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/guilds/{guild_id}/channels/{channel_id}/permissions/@me")

    # ---------- 角色与成员角色（反应角色 / 验证门） ----------

    def roles(self, guild_id: str) -> List[Dict[str, Any]]:
        result = self._request("GET", f"/guilds/{guild_id}/roles")
        return result if isinstance(result, list) else []

    def role(self, guild_id: str, role_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/guilds/{guild_id}/roles/{role_id}")

    def create_role(
        self,
        guild_id: str,
        name: str,
        *,
        permissions: int = 0,
        position: int = 1,
        color: Optional[str] = None,
        hoist: Optional[bool] = None,
        mentionable: Optional[bool] = None,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {"name": name, "permissions": permissions, "position": position}
        if color is not None:
            body["color"] = color
        if hoist is not None:
            body["hoist"] = hoist
        if mentionable is not None:
            body["mentionable"] = mentionable
        return self._request("POST", f"/guilds/{guild_id}/roles", body)

    def update_role(
        self,
        guild_id: str,
        role_id: str,
        name: str,
        *,
        permissions: int = 0,
        position: int = 1,
        color: Optional[str] = None,
        hoist: Optional[bool] = None,
        mentionable: Optional[bool] = None,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {"name": name, "permissions": permissions, "position": position}
        if color is not None:
            body["color"] = color
        if hoist is not None:
            body["hoist"] = hoist
        if mentionable is not None:
            body["mentionable"] = mentionable
        return self._request("PATCH", f"/guilds/{guild_id}/roles/{role_id}", body)

    def delete_role(self, guild_id: str, role_id: str) -> None:
        self._request("DELETE", f"/guilds/{guild_id}/roles/{role_id}")

    def add_member_role(self, guild_id: str, member_id: str, role_id: str) -> Dict[str, Any]:
        """给成员绑定角色；member_id 接受 members.id 或 user_id。"""
        return self._request("PUT", f"/guilds/{guild_id}/members/{member_id}/roles/{role_id}")

    def remove_member_role(self, guild_id: str, member_id: str, role_id: str) -> None:
        self._request("DELETE", f"/guilds/{guild_id}/members/{member_id}/roles/{role_id}")

    # ---------- 频道权限覆盖（验证门搭建） ----------

    def overwrites(self, guild_id: str, channel_id: str) -> List[Dict[str, Any]]:
        result = self._request("GET", f"/guilds/{guild_id}/channels/{channel_id}/overwrites")
        return result if isinstance(result, list) else []

    def set_overwrite(
        self,
        guild_id: str,
        channel_id: str,
        target_id: str,
        *,
        type: str,
        allow: int = 0,
        deny: int = 0,
    ) -> Dict[str, Any]:
        return self._request(
            "PUT",
            f"/guilds/{guild_id}/channels/{channel_id}/overwrites/{target_id}",
            {"type": type, "allow": allow, "deny": deny},
        )

    def delete_overwrite(
        self, guild_id: str, channel_id: str, target_id: str, *, type: Optional[str] = None
    ) -> None:
        query = f"?type={urllib.parse.quote(type)}" if type else ""
        self._request("DELETE", f"/guilds/{guild_id}/channels/{channel_id}/overwrites/{target_id}{query}")

    # ---------- 服务器 / 频道结构 ----------

    def guild(self, guild_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/guilds/{guild_id}")

    def update_guild(self, guild_id: str, **body: Any) -> Dict[str, Any]:
        return self._request("PATCH", f"/guilds/{guild_id}", body)

    def channel(self, channel_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/channels/{channel_id}")

    def create_channel(self, guild_id: str, **body: Any) -> Dict[str, Any]:
        return self._request("POST", f"/guilds/{guild_id}/channels", body)

    def update_channel(self, channel_id: str, **body: Any) -> Dict[str, Any]:
        return self._request("PATCH", f"/channels/{channel_id}", body)

    def delete_channel(self, channel_id: str) -> None:
        self._request("DELETE", f"/channels/{channel_id}")

    # ---------- 成员治理 ----------

    def kick_member(self, guild_id: str, member_id: str) -> None:
        """踢出成员；member_id=@me 时为 bot 主动退服。"""
        self._request("DELETE", f"/guilds/{guild_id}/members/{member_id}")

    def leave_guild(self, guild_id: str) -> None:
        self.kick_member(guild_id, "@me")

    def update_member(self, guild_id: str, member_id: str, **body: Any) -> Dict[str, Any]:
        return self._request("PATCH", f"/guilds/{guild_id}/members/{member_id}", body)

    def ban_user(self, guild_id: str, user_id: str, *, reason: Optional[str] = None) -> None:
        body: Dict[str, Any] = {}
        if reason is not None:
            body["reason"] = reason
        self._request("PUT", f"/guilds/{guild_id}/bans/{user_id}", body)

    def unban_user(self, guild_id: str, user_id: str) -> None:
        self._request("DELETE", f"/guilds/{guild_id}/bans/{user_id}")

    def bans(self, guild_id: str) -> Any:
        return self._request("GET", f"/guilds/{guild_id}/bans")

    def create_invite(
        self, guild_id: str, *, ttl_seconds: Optional[int] = None, max_uses: Optional[int] = None
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {}
        if ttl_seconds:
            body["ttl_seconds"] = ttl_seconds
        if max_uses:
            body["max_uses"] = max_uses
        return self._request("POST", f"/guilds/{guild_id}/invites", body)

    def invites(self, guild_id: str) -> Any:
        return self._request("GET", f"/guilds/{guild_id}/invites")

    def delete_invite(self, code: str) -> None:
        self._request("DELETE", f"/invites/{code}")

    # ---------- Restriction / 审计 / 语音管理 ----------

    def create_restriction(self, guild_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", f"/guilds/{guild_id}/restrictions", body)

    def restrictions(self, guild_id: str) -> Any:
        return self._request("GET", f"/guilds/{guild_id}/restrictions")

    def lift_restriction(self, guild_id: str, restriction_id: str) -> None:
        self._request("DELETE", f"/guilds/{guild_id}/restrictions/{restriction_id}")

    def audit_logs(self, guild_id: str) -> Any:
        return self._request("GET", f"/guilds/{guild_id}/audit-logs")

    def voice_disconnect(self, guild_id: str, body: Dict[str, Any]) -> None:
        self._request("POST", f"/guilds/{guild_id}/voice/disconnect", body)

    def voice_move(self, guild_id: str, body: Dict[str, Any]) -> None:
        self._request("POST", f"/guilds/{guild_id}/voice/move", body)

    def update_voice_state(self, guild_id: str, user_id: str, body: Dict[str, Any]) -> None:
        self._request("PATCH", f"/guilds/{guild_id}/voice/states/{user_id}", body)

    # ---------- 消息 ----------

    def send_message(
        self,
        channel_id: str,
        content: Optional[str] = None,
        *,
        card: Optional[Dict[str, Any]] = None,
        reply_to_id: Optional[str] = None,
        attachment_ids: Optional[Iterable[str]] = None,
        nonce: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._request(
            "POST",
            f"/channels/{channel_id}/messages",
            {
                "content": content or "",
                "card": card,
                "reply_to_id": reply_to_id or "",
                "attachment_ids": list(attachment_ids or []),
                "nonce": nonce or uuid.uuid4().hex,
            },
        )

    def send_card(self, channel_id: str, card: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        return self.send_message(channel_id, card=card, **kwargs)

    def get_messages(
        self, channel_id: str, *, before: Optional[str] = None, after: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        params = {k: v for k, v in {"before": before, "after": after, "limit": limit}.items() if v}
        query = f"?{urllib.parse.urlencode(params)}" if params else ""
        return self._request("GET", f"/channels/{channel_id}/messages{query}").get("messages", [])

    def get_message(self, channel_id: str, message_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/channels/{channel_id}/messages/{message_id}")

    def edit_message(self, channel_id: str, message_id: str, content: str) -> Dict[str, Any]:
        return self._request("PATCH", f"/channels/{channel_id}/messages/{message_id}", {"content": content})

    def delete_message(self, channel_id: str, message_id: str) -> None:
        self._request("DELETE", f"/channels/{channel_id}/messages/{message_id}")

    def add_reaction(self, channel_id: str, message_id: str, emoji: str) -> None:
        self._request("PUT", f"/channels/{channel_id}/messages/{message_id}/reactions/{urllib.parse.quote(emoji)}/@me")

    def remove_reaction(self, channel_id: str, message_id: str, emoji: str) -> None:
        self._request(
            "DELETE", f"/channels/{channel_id}/messages/{message_id}/reactions/{urllib.parse.quote(emoji)}/@me"
        )

    def list_reaction_users(self, channel_id: str, message_id: str, emoji: str) -> List[Dict[str, Any]]:
        return self._request(
            "GET", f"/channels/{channel_id}/messages/{message_id}/reactions/{urllib.parse.quote(emoji)}"
        ).get("users", [])

    def typing(self, channel_id: str) -> None:
        self._request("POST", f"/channels/{channel_id}/typing")

    def search_messages(
        self, query: str, *, guild_id: Optional[str] = None, channel_id: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        params = {"q": query}
        if guild_id:
            params["guild_id"] = guild_id
        if channel_id:
            params["channel_id"] = channel_id
        if limit:
            params["limit"] = str(limit)
        return self._request("GET", f"/search/messages?{urllib.parse.urlencode(params)}").get("messages", [])

    # ---------- 流式消息 ----------

    def start_stream(
        self, channel_id: str, *, content: Optional[str] = None, reply_to_id: Optional[str] = None
    ) -> MessageStream:
        message = self._request(
            "POST",
            f"/channels/{channel_id}/messages/stream",
            {"content": content or "", "reply_to_id": reply_to_id or "", "nonce": uuid.uuid4().hex},
        )
        return MessageStream(self, channel_id, message)

    # ---------- 语音 ----------

    def join_voice(
        self, guild_id: str, channel_id: str, *, self_mute: bool = False, self_deaf: bool = False
    ) -> Dict[str, Any]:
        """加入语音频道。返回含 Media Token（bot=true claim）、SFU 信令地址、caps 等。

        机器人拥有独立音频权限（由其绑定角色决定），并在音频流参与者信令中
        带 is_bot 独立标记。token TTL 2-5 分钟，需周期调用 refresh_voice_token。
        """
        return self._request(
            "POST",
            "/voice/join",
            {"guild_id": guild_id, "channel_id": channel_id, "self_mute": self_mute, "self_deaf": self_deaf},
        )

    def leave_voice(self, guild_id: str) -> Dict[str, Any]:
        return self._request("POST", "/voice/leave", {"guild_id": guild_id})

    def refresh_voice_token(self, guild_id: str) -> Dict[str, Any]:
        return self._request("POST", "/voice/refresh-token", {"guild_id": guild_id})

    def voice_states(self, guild_id: str, channel_id: str) -> List[Dict[str, Any]]:
        return self._request("GET", f"/guilds/{guild_id}/channels/{channel_id}/voice-states").get("voice_states", [])

    # ---------- 扩展：排序 / 解锁 / 资源 / 消息 / 舞台 / 贴图 ----------

    def reorder_channels(self, guild_id: str, entries: Any) -> None:
        self._request("PATCH", f"/guilds/{guild_id}/channels", entries)

    def unlock_channel(self, channel_id: str, password: str) -> Dict[str, Any]:
        return self._request("POST", f"/channels/{channel_id}/unlock", {"password": password})

    def unlock_status(self, channel_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/channels/{channel_id}/unlock-status")

    def reorder_roles(self, guild_id: str, entries: Any) -> None:
        self._request("PATCH", f"/guilds/{guild_id}/roles", entries)

    def upload_guild_icon(self, guild_id: str, data: bytes, filename: str = "icon.png") -> Dict[str, Any]:
        return self._upload_multipart("POST", f"/guilds/{guild_id}/icon", data, filename)

    def upload_guild_icon_file(self, guild_id: str, path: str) -> Dict[str, Any]:
        """从本地路径上传服务器图标。"""
        return self._upload_file_path("POST", f"/guilds/{guild_id}/icon", path)

    def delete_guild_icon(self, guild_id: str) -> None:
        self._request("DELETE", f"/guilds/{guild_id}/icon")

    def upload_guild_banner(self, guild_id: str, data: bytes, filename: str = "banner.png") -> Dict[str, Any]:
        return self._upload_multipart("POST", f"/guilds/{guild_id}/banner", data, filename)

    def upload_guild_banner_file(self, guild_id: str, path: str) -> Dict[str, Any]:
        return self._upload_file_path("POST", f"/guilds/{guild_id}/banner", path)

    def delete_guild_banner(self, guild_id: str) -> None:
        self._request("DELETE", f"/guilds/{guild_id}/banner")

    def banners(self, guild_id: str) -> Any:
        return self._request("GET", f"/guilds/{guild_id}/banners")

    def add_banner(self, guild_id: str, data: bytes, filename: str = "banner.png") -> Dict[str, Any]:
        return self._upload_multipart("POST", f"/guilds/{guild_id}/banners", data, filename)

    def add_banner_file(self, guild_id: str, path: str) -> Dict[str, Any]:
        return self._upload_file_path("POST", f"/guilds/{guild_id}/banners", path)

    def reorder_banners(self, guild_id: str, body: Any) -> None:
        self._request("PATCH", f"/guilds/{guild_id}/banners", body)

    def remove_banner(self, guild_id: str, banner_id: str) -> None:
        self._request("DELETE", f"/guilds/{guild_id}/banners/{banner_id}")

    def update_name_style(self, guild_id: str, member_id: str, **body: Any) -> Dict[str, Any]:
        return self._request("PATCH", f"/guilds/{guild_id}/members/{member_id}/name-style", body)

    def invite(self, code: str) -> Dict[str, Any]:
        return self._request("GET", f"/invites/{code}")

    def preview_invite(self, code: str) -> Dict[str, Any]:
        return self._request("GET", f"/invites/{code}/preview")

    def delete_guild_invite(self, guild_id: str, code: str) -> None:
        self._request("DELETE", f"/guilds/{guild_id}/invites/{code}")

    def restriction(self, guild_id: str, restriction_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/guilds/{guild_id}/restrictions/{restriction_id}")

    def update_restriction(self, guild_id: str, restriction_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PATCH", f"/guilds/{guild_id}/restrictions/{restriction_id}", body)

    def list_edits(self, channel_id: str, message_id: str) -> Any:
        return self._request("GET", f"/channels/{channel_id}/messages/{message_id}/edits")

    def ack_message(self, channel_id: str, message_id: str) -> None:
        self._request("POST", f"/channels/{channel_id}/messages/{message_id}/ack", {})

    def ack_channel(self, channel_id: str, body: Optional[Dict[str, Any]] = None) -> None:
        self._request("POST", f"/channels/{channel_id}/ack", body or {})

    def ack_guild(self, guild_id: str) -> None:
        self._request("POST", f"/guilds/{guild_id}/ack", {})

    def read_states(self) -> Any:
        return self._request("GET", "/users/@me/read-states")

    def presign_attachment(self, channel_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", f"/channels/{channel_id}/attachments/presign", body)

    def upload_limit(self, guild_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/guilds/{guild_id}/upload-limit")

    def voice_packs(self, guild_id: str) -> Any:
        return self._request("GET", f"/guilds/{guild_id}/voice-packs")

    def create_voice_pack(self, guild_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", f"/guilds/{guild_id}/voice-packs", body)

    def patch_voice_pack(self, guild_id: str, pack_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PATCH", f"/guilds/{guild_id}/voice-packs/{pack_id}", body)

    def delete_voice_pack(self, guild_id: str, pack_id: str) -> None:
        self._request("DELETE", f"/guilds/{guild_id}/voice-packs/{pack_id}")

    def upload_voice_pack_audio(
        self, guild_id: str, pack_id: str, data: bytes, filename: str = "pack.ogg"
    ) -> Dict[str, Any]:
        return self._upload_multipart("POST", f"/guilds/{guild_id}/voice-packs/{pack_id}/audio", data, filename)

    def upload_voice_pack_audio_file(self, guild_id: str, pack_id: str, path: str) -> Dict[str, Any]:
        return self._upload_file_path("POST", f"/guilds/{guild_id}/voice-packs/{pack_id}/audio", path)

    def select_voice_pack(self, guild_id: str, pack_id: str) -> None:
        self._request("PUT", f"/guilds/{guild_id}/voice-packs/{pack_id}/select", {})

    def my_voice_pack(self, guild_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/guilds/{guild_id}/voice-packs/@me")

    def clear_my_voice_pack(self, guild_id: str) -> None:
        self._request("DELETE", f"/guilds/{guild_id}/voice-packs/@me")

    def guild_voice_pack_config(self, guild_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/guilds/{guild_id}/voice-pack")

    def patch_guild_voice_pack_config(self, guild_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PATCH", f"/guilds/{guild_id}/voice-pack", body)

    def channel_voice_pack_config(self, guild_id: str, channel_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/guilds/{guild_id}/channels/{channel_id}/voice-pack")

    def put_channel_voice_pack_config(
        self, guild_id: str, channel_id: str, body: Dict[str, Any]
    ) -> Dict[str, Any]:
        return self._request("PUT", f"/guilds/{guild_id}/channels/{channel_id}/voice-pack", body)

    def patch_self_voice_state(
        self, guild_id: str, *, self_mute: Optional[bool] = None, self_deaf: Optional[bool] = None
    ) -> None:
        body: Dict[str, Any] = {"guild_id": guild_id}
        if self_mute is not None:
            body["self_mute"] = self_mute
        if self_deaf is not None:
            body["self_deaf"] = self_deaf
        self._request("PATCH", "/voice/state", body)

    def voice_nodes(self, guild_id: str) -> Any:
        return self._request("GET", f"/guilds/{guild_id}/voice/nodes")

    def voice_public_key(self) -> Dict[str, Any]:
        return self._request("GET", "/voice/public-key")

    def report_voice_rtt(self, body: Dict[str, Any]) -> None:
        self._request("POST", "/voice/rtt", body)

    def report_ice_failed(self, body: Dict[str, Any]) -> None:
        self._request("POST", "/voice/ice-failed", body)

    def ack_migration(self, migration_id: str, body: Optional[Dict[str, Any]] = None) -> None:
        self._request("POST", f"/voice/migrations/{migration_id}/ack", body or {})

    def get_voice_stage(self, channel_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/channels/{channel_id}/voice-stage")

    def patch_voice_stage(self, channel_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PATCH", f"/channels/{channel_id}/voice-stage", body)

    def stage_queue(self, channel_id: str) -> Any:
        return self._request("GET", f"/channels/{channel_id}/stage/queue")

    def stage_remove_from_queue(self, channel_id: str, user_id: str) -> None:
        self._request("DELETE", f"/channels/{channel_id}/stage/queue/{user_id}")

    def stage_apply(self, channel_id: str) -> None:
        self._request("POST", f"/channels/{channel_id}/stage/apply", {})

    def stage_cancel_apply(self, channel_id: str) -> None:
        self._request("DELETE", f"/channels/{channel_id}/stage/apply")

    def stage_bring_up(self, channel_id: str, body: Optional[Dict[str, Any]] = None) -> None:
        self._request("POST", f"/channels/{channel_id}/stage/bring-up", body or {})

    def stage_bring_down(self, channel_id: str, body: Optional[Dict[str, Any]] = None) -> None:
        self._request("POST", f"/channels/{channel_id}/stage/bring-down", body or {})

    def stage_self_leave(self, channel_id: str) -> None:
        self._request("POST", f"/channels/{channel_id}/stage/self-leave", {})

    def screen_start(self, channel_id: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._request("POST", f"/channels/{channel_id}/voice/screen/start", body or {})

    def screen_stop(self, channel_id: str) -> None:
        self._request("POST", f"/channels/{channel_id}/voice/screen/stop", {})

    def screen_stop_user(self, channel_id: str, body: Dict[str, Any]) -> None:
        self._request("POST", f"/channels/{channel_id}/voice/screen/stop-user", body)

    def screen_quota(self, guild_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/guilds/{guild_id}/screen-quota")

    def my_sticker_packs(self) -> Any:
        return self._request("GET", "/users/@me/sticker-packs")

    def create_sticker_pack(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/users/@me/sticker-packs", body)

    def patch_sticker_pack(self, pack_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PATCH", f"/users/@me/sticker-packs/{pack_id}", body)

    def delete_sticker_pack(self, pack_id: str) -> None:
        self._request("DELETE", f"/users/@me/sticker-packs/{pack_id}")

    def restore_sticker_pack(self, pack_id: str) -> None:
        self._request("POST", f"/users/@me/sticker-packs/{pack_id}/restore", {})

    def upload_sticker_pack_cover(
        self, pack_id: str, data: bytes, filename: str = "cover.png"
    ) -> Dict[str, Any]:
        return self._upload_multipart("PUT", f"/users/@me/sticker-packs/{pack_id}/cover", data, filename)

    def upload_sticker_pack_cover_file(self, pack_id: str, path: str) -> Dict[str, Any]:
        return self._upload_file_path("PUT", f"/users/@me/sticker-packs/{pack_id}/cover", path)

    def delete_sticker_pack_cover(self, pack_id: str) -> None:
        self._request("DELETE", f"/users/@me/sticker-packs/{pack_id}/cover")

    def upload_sticker_item(
        self, pack_id: str, data: bytes, filename: str = "item.png"
    ) -> Dict[str, Any]:
        return self._upload_multipart("POST", f"/users/@me/sticker-packs/{pack_id}/items", data, filename)

    def upload_sticker_item_file(self, pack_id: str, path: str) -> Dict[str, Any]:
        return self._upload_file_path("POST", f"/users/@me/sticker-packs/{pack_id}/items", path)

    def patch_sticker_item(self, pack_id: str, item_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PATCH", f"/users/@me/sticker-packs/{pack_id}/items/{item_id}", body)

    def delete_sticker_item(self, pack_id: str, item_id: str) -> None:
        self._request("DELETE", f"/users/@me/sticker-packs/{pack_id}/items/{item_id}")

    def copy_sticker_item(self, pack_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", f"/users/@me/sticker-packs/{pack_id}/items/copy", body)

    def sticker_library(self) -> Any:
        return self._request("GET", "/users/@me/sticker-library")

    def install_sticker_pack(self, pack_id: str) -> None:
        self._request("PUT", f"/users/@me/sticker-library/{pack_id}", {})

    def uninstall_sticker_pack(self, pack_id: str) -> None:
        self._request("DELETE", f"/users/@me/sticker-library/{pack_id}")

    def sticker_available(self, guild_id: Optional[str] = None) -> Any:
        q = f"?guild_id={urllib.parse.quote(guild_id)}" if guild_id else ""
        return self._request("GET", f"/users/@me/sticker-available{q}")

    def sticker_pack(self, pack_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/sticker-packs/{pack_id}")

    def sticker_item(self, item_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/sticker-items/{item_id}")

    def sticker_pack_bans(self, guild_id: str) -> Any:
        return self._request("GET", f"/guilds/{guild_id}/sticker-pack-bans")

    def ban_sticker_pack(self, guild_id: str, pack_id: str) -> None:
        self._request("PUT", f"/guilds/{guild_id}/sticker-pack-bans/{pack_id}", {})

    def unban_sticker_pack(self, guild_id: str, pack_id: str) -> None:
        self._request("DELETE", f"/guilds/{guild_id}/sticker-pack-bans/{pack_id}")

    def _upload_file_path(self, method: str, api_path: str, file_path: str) -> Dict[str, Any]:
        """从本地路径读取文件并 multipart 上传（字段名 file）。"""
        import os

        with open(file_path, "rb") as f:
            data = f.read()
        return self._upload_multipart(method, api_path, data, os.path.basename(file_path))

    def upload_file(self, method: str, api_path: str, file_path: str) -> Dict[str, Any]:
        """通用路径上传：method + API path + 本地文件路径。"""
        return self._upload_file_path(method, api_path, file_path)

    def _upload_multipart(self, method: str, path: str, data: bytes, filename: str) -> Dict[str, Any]:
        boundary = f"----OwlBot{uuid.uuid4().hex}"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n"
        ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
        request = urllib.request.Request(self.api_base + path, data=body, method=method)
        request.add_header("Authorization", f"Bot {self.token}")
        request.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                if response.status == 204:
                    return {}
                return json.loads(response.read() or b"{}")
        except urllib.error.HTTPError as exc:
            try:
                payload = json.loads(exc.read() or b"{}")
            except Exception:
                payload = {}
            error = payload.get("error") or {}
            raise OwlBotError(exc.code, error.get("code"), error.get("message")) from None

    # ---------- Gateway ----------

    @property
    def gateway_url(self) -> str:
        scheme = "wss" if self.api_base.startswith("https") else "ws"
        return scheme + self.api_base[self.api_base.index("://"):] + "/gateway"


async def run_gateway(
    client: OwlBotClient,
    on_event: Callable[[str, Any], Any],
    *,
    reconnect: bool = True,
) -> None:
    """连接 Gateway 并把 DISPATCH 事件回调给 on_event(event_type, payload)。

    需要可选依赖 websockets（pip install owlspeak-bot[gateway]）。
    on_event 可为普通函数或协程；内置事件 "READY" 也会回调。
    """
    try:
        import websockets
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Gateway 需要 websockets：pip install owlspeak-bot[gateway]") from exc

    backoff = 1.0
    while True:
        try:
            async with websockets.connect(client.gateway_url) as ws:
                heartbeat_task: Optional[asyncio.Task] = None
                async for raw in ws:
                    frame = json.loads(raw)
                    op = frame.get("op")
                    if op == "HELLO":
                        await ws.send(json.dumps({"op": "IDENTIFY", "d": {"token": client.token}}))
                        interval = (frame.get("d") or {}).get("heartbeat_interval_ms", 30000) / 1000

                        async def beat() -> None:
                            while True:
                                await asyncio.sleep(interval)
                                await ws.send(json.dumps({"op": "HEARTBEAT"}))

                        heartbeat_task = asyncio.create_task(beat())
                    elif op == "READY":
                        backoff = 1.0
                        result = on_event("READY", frame.get("d"))
                        if asyncio.iscoroutine(result):
                            await result
                    elif op == "DISPATCH":
                        result = on_event(frame.get("t", ""), frame.get("d"))
                        if asyncio.iscoroutine(result):
                            await result
                if heartbeat_task:
                    heartbeat_task.cancel()
        except asyncio.CancelledError:
            raise
        except Exception:
            if not reconnect:
                raise
        if not reconnect:
            return
        await asyncio.sleep(backoff)
        backoff = min(backoff * 2, 30.0)
