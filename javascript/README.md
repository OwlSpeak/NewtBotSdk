# @owlspeak/bot-sdk（JavaScript / TypeScript SDK）

OwlSpeak 机器人开放平台官方 JS SDK。零依赖，要求 Node ≥ 21（原生 `fetch` 与 `WebSocket`）。

本包位于 monorepo **[OwlBotSdk](https://github.com/owlspeak/OwlBotSdk)** 的 `javascript/` 目录。

## 安装

```bash
# 发布到 npm 后
npm install @owlspeak/bot-sdk

# 本地 monorepo
# package.json: "@owlspeak/bot-sdk": "file:../OwlBotSdk/javascript"
```

## 快速上手：一个会流式回复的 AI 机器人

```js
import { OwlBotClient } from "@owlspeak/bot-sdk"

const bot = new OwlBotClient({
  baseUrl: "https://owl.example.com",
  token: process.env.OWL_BOT_TOKEN, // owlbot_xxx，控制台签发
})

// 1. 实时事件：监听新消息
const gateway = bot.connectGateway()
gateway.on("ready", data => console.log("已连接，机器人：", data.user.username))

gateway.on("MESSAGE_CREATE", async message => {
  if (message.author_is_bot) return // 忽略机器人消息，防止自我循环
  if (!message.content.startsWith("!ask ")) return

  // 2. 打字指示 + 流式回复（对接你的 LLM）
  await bot.typing(message.channel_id)
  const stream = await bot.startStream(message.channel_id, { replyToId: message.id })
  for await (const chunk of askLLM(message.content.slice(5))) {
    await stream.append(chunk)
  }
  await stream.end({
    card: { title: "回答完毕", footer: "AI Bot", color: "#6366f1" },
  })
})

// 3. 卡片消息
await bot.sendCard(channelId, {
  title: "部署完成",
  description: "v1.4.2 已发布",
  color: "#22c55e",
  fields: [{ name: "耗时", value: "42s", inline: true }],
})
```

## 语音接入

```js
// 机器人拥有独立的音频权限（由其在服务器内绑定的角色决定），
// 无需客户端或用户账号；在音频流中带 is_bot 独立标记。
const voice = await bot.joinVoice(guildId, voiceChannelId)
// voice.token           → Media Token（bot=true claim）
// voice.advertise_wss_url → SFU 信令地址：auth → ready → offer/answer/ice → WebRTC 音频
// token TTL 2-5 分钟，周期调用 bot.refreshVoiceToken(guildId) 并经信令 auth 帧续签

await bot.leaveVoice(guildId)
```

WebRTC 媒体层可用 [werift](https://github.com/shinyoshiaki/werift-webrtc) 等纯 JS WebRTC 实现，
或参考 Go SDK + pion 的完整示例。

## API 摘要

- 消息：`sendMessage` / `sendCard` / `getMessages` / `getMessage` / `editMessage` / `deleteMessage` / `addReaction` / `removeReaction` / `listReactionUsers` / `typing` / `searchMessages`
- 流式：`startStream(channelId)` → `stream.append(delta)` → `stream.end({content?, card?})`
- 角色（反应角色 / 验证门）：`roles` / `role` / `createRole` / `updateRole` / `deleteRole` / `addMemberRole` / `removeMemberRole`
- 覆盖：`overwrites` / `setOverwrite` / `deleteOverwrite` / `channelPermissions`
- 语音：`joinVoice` / `leaveVoice` / `refreshVoiceToken` / `voiceStates`
- 资源：`me` / `guilds` / `channels` / `members` / `member` / `permissions`
- 事件：`connectGateway()` → `gw.on("MESSAGE_CREATE" | "MESSAGE_REACTION_ADD" | "MESSAGE_STREAM_DELTA" | ... , handler)`

## 反应角色（验证门）示例

```js
const RULES_MESSAGE_ID = process.env.RULES_MESSAGE_ID
const VERIFIED_ROLE_ID = process.env.VERIFIED_ROLE_ID

const gw = bot.connectGateway()
gw.on("MESSAGE_REACTION_ADD", async (ev) => {
  if (String(ev.message_id) !== RULES_MESSAGE_ID || ev.emoji !== "✅") return
  await bot.addMemberRole(ev.guild_id, ev.user_id, VERIFIED_ROLE_ID)
})
gw.on("MESSAGE_REACTION_REMOVE", async (ev) => {
  if (String(ev.message_id) !== RULES_MESSAGE_ID || ev.emoji !== "✅") return
  await bot.removeMemberRole(ev.guild_id, ev.user_id, VERIFIED_ROLE_ID)
})
```

安装后需给 bot 绑定带 `MANAGE_ROLES` 的角色，且层级高于「已验证」角色。完整协议与权限位说明见 [`../README.md`](../README.md)。
