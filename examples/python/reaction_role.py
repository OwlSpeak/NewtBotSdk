"""反应角色最小示例。"""

from __future__ import annotations

import asyncio
import os

from newtspeak_bot import OwlBotClient, run_gateway

bot = OwlBotClient(os.environ["NEWT_BASE_URL"], token=os.environ["NEWT_BOT_TOKEN"])
RULES_MESSAGE_ID = os.environ["RULES_MESSAGE_ID"]
VERIFIED_ROLE_ID = os.environ["VERIFIED_ROLE_ID"]


async def on_event(event: str, data: dict) -> None:
    if event == "READY":
        print("已连接", (data or {}).get("user", {}).get("username"))
        return
    if event != "MESSAGE_REACTION_ADD":
        return
    if str(data.get("message_id")) != RULES_MESSAGE_ID or data.get("emoji") != "✅":
        return
    try:
        bot.add_member_role(data["guild_id"], data["user_id"], VERIFIED_ROLE_ID)
        print("已赋角", data["user_id"])
    except Exception as exc:  # noqa: BLE001
        print("赋角失败", exc)


if __name__ == "__main__":
    asyncio.run(run_gateway(bot, on_event))
