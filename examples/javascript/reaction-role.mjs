/**
 * 反应角色最小示例。
 *
 *   export NEWT_BASE_URL=https://newt.example.com
 *   export NEWT_BOT_TOKEN=newtbot_xxx
 *   export RULES_MESSAGE_ID=...
 *   export VERIFIED_ROLE_ID=...
 *   node examples/javascript/reaction-role.mjs
 */

import { OwlBotClient } from "../../javascript/index.js"

const bot = new OwlBotClient({
  baseUrl: process.env.NEWT_BASE_URL,
  token: process.env.NEWT_BOT_TOKEN,
})

const RULES_MESSAGE_ID = process.env.RULES_MESSAGE_ID
const VERIFIED_ROLE_ID = process.env.VERIFIED_ROLE_ID

const gw = bot.connectGateway()
gw.on("ready", (data) => console.log("已连接", data?.user?.username))
gw.on("MESSAGE_REACTION_ADD", async (ev) => {
  if (String(ev.message_id) !== RULES_MESSAGE_ID || ev.emoji !== "✅") return
  try {
    await bot.addMemberRole(ev.guild_id, ev.user_id, VERIFIED_ROLE_ID)
    console.log("已赋角", ev.user_id)
  } catch (err) {
    console.error("赋角失败", err)
  }
})
