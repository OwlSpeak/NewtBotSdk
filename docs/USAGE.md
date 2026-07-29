# NewtBotSdk 使用文档

机器人官方多语言 SDK。以 **bot token** 调用 `/bot-api/v1`，权限与人类成员同一套 RBAC。

> 协议细节见 [HTTP-API.md](./HTTP-API.md) · 完整协议 [API.md](./API.md)

## 与 Agent 的区别

| | Bot SDK | Agent CLI |
|--|---------|-----------|
| 身份 | 机器人（`IsBot=true`） | 真人 OAuth 用户 |
| 凭证 | `newtbot_…` token | 设备码 / PKCE |
| 平面 | `/bot-api/v1` | `/gapi/v1`（+ 可选 `/api/v1`） |
| 场景 | 自动化、反应角色、卡片交互 | 运维、AI Skill、MCP |

## 1. 准备 Token

1. 管理控制台 → **开放平台 / 机器人** → 创建机器人  
2. **Token 管理** → 签发（明文仅一次，形如 `newtbot_xxx`）  
3. **安装到服务器**，绑定角色（按需 `SEND_MESSAGES` / `MANAGE_ROLES` / `KICK_MEMBERS` 等）

```text
Authorization: Bot <token>
Base:     https://<server>/bot-api/v1
Gateway:  wss://<server>/bot-api/v1/gateway
限流:     20 QPS / bot（突发 40）→ 429
```

## 2. 安装

| 语言 | 安装 |
|------|------|
| **JS/TS** | `npm i @newtspeak/bot-sdk` 或 monorepo `file:../NewtBotSdk/javascript`（Node ≥ 21） |
| **Go** | `go get github.com/NewtSpeak/NewtBotSdk/go@latest` |
| **Python** | `pip install -e "./NewtBotSdk/python[gateway]"` |
| **Rust** | `newtspeak-bot = { path = "NewtBotSdk/rust" }` + tokio |

## 3. 最小示例

### JavaScript

```js
import { OwlBotClient } from "@newtspeak/bot-sdk"

const bot = new OwlBotClient({
  baseUrl: "https://newt-panel.example.com",
  token: process.env.NEWT_BOT_TOKEN,
})

await bot.sendText(channelId, "你好！")

const gw = bot.connectGateway()
gw.on("MESSAGE_CREATE", (msg) => {
  if (msg.author_is_bot) return
  console.log(msg.content)
})
gw.on("interaction", async (i) => {
  await i.reply("收到", { ephemeral: true })
})
```

### Go

```go
bot := owlbot.New("https://newt-panel.example.com", os.Getenv("NEWT_BOT_TOKEN"))
_, _ = bot.SendText(channelID, "你好！")

gw := bot.ConnectGateway()
gw.On("MESSAGE_CREATE", func(raw json.RawMessage) { /* ... */ })
gw.OnInteraction(func(i *owlbot.Interaction) {
  _, _ = i.ReplyText("收到")
})
select {}
```

### Python

```python
from newtspeak_bot import OwlBotClient, run_gateway
import asyncio, os

bot = OwlBotClient("https://newt-panel.example.com", token=os.environ["NEWT_BOT_TOKEN"])
bot.send_message(channel_id, "你好！")

async def on_event(event, data):
    if event == "MESSAGE_CREATE":
        print(data.get("content"))

asyncio.run(run_gateway(bot, on_event))
```

### Rust

```rust
let bot = Client::new("https://newt-panel.example.com", std::env::var("NEWT_BOT_TOKEN")?)?;
bot.send_text(&channel_id, "你好！").await?;
```

## 4. 常见能力

### 发消息 / 卡片 / ephemeral

```js
await bot.sendText(cid, "纯文本")
await bot.sendCard(cid, {
  title: "部署完成",
  color: "#22c55e",
  buttons: [
    { label: "批准", custom_id: "approve:1", style: "success" },
    { label: "日志", url: "https://ci.example/1" },
  ],
})
await bot.sendEphemeral(cid, userId, "仅你可见")
```

### 流式（对接 LLM）

```go
_ = bot.Typing(channelID)
s, _ := bot.StartStream(channelID, "")
_ = s.Append("思考中…")
_, _ = s.End(map[string]any{"footer": "AI"})
```

### 反应角色

```js
gw.on("MESSAGE_REACTION_ADD", async (ev) => {
  if (String(ev.message_id) !== RULES_ID || ev.emoji !== "✅") return
  await bot.addMemberRole(ev.guild_id, ev.user_id, ROLE_ID)
})
```

需 `MANAGE_ROLES`，且 bot 角色层级 **高于** 目标角色。

### 按钮交互

1. 发带 `custom_id` 的卡片  
2. Gateway 收 `INTERACTION_CREATE`（SDK 包装为 `interaction`）  
3. **15 分钟内** `ack` / `reply` / `updateMessage`  

```js
gw.on("interaction", async (i) => {
  if (i.customId.startsWith("approve:")) {
    await i.updateMessage({ card: { title: "已批准 ✅" } })
  } else {
    await i.ack() // defer，稍后再 reply
  }
})
```

### 语音（拿 Media Token）

```go
v, err := bot.JoinVoice(guildID, voiceChannelID)
// v.Token → Media Token；v.AdvertiseWSSURL → SFU 信令
// 媒体层参考 Newt-SFU/cmd/loadbot（pion）
defer bot.LeaveVoice(guildID)
```

### 文件上传

```go
bot.UploadGuildIconFile(gid, "./icon.png")
bot.UploadStickerItemFile(packID, "./wave.png")
```

```js
await bot.uploadGuildIconFile(gid, "./icon.png")
```

## 5. 示例仓库

| 路径 | 内容 |
|------|------|
| `NewtBotSdk/examples/go/` | 反应角色 |
| `NewtBotSdk/examples/javascript/` | 同上 |
| `NewtBotSdk/examples/python/` | 同上 |
| `NewtBotSdk/examples/rust/` | 同上 |

```bash
export NEWT_BASE_URL=https://newt-panel.example.com
export NEWT_BOT_TOKEN=newtbot_xxx
export RULES_MESSAGE_ID=...
export VERIFIED_ROLE_ID=...
cd NewtBotSdk/examples/go && go run .
```

## 6. 排障

| 现象 | 处理 |
|------|------|
| 401 | token 失效 / 头不是 `Bot ` 或 `Bearer ` |
| 403 | 角色权限不足或层级不够 |
| 429 | 降速；遵守 20 QPS |
| Gateway 无事件 | 检查 WSS 路径；频道是否对 bot 可见 |
| 交互 410 | 超过 15 分钟未 callback |
| 交互 409 | 已回应过（ack 后最多再补一次） |

## 7. 相关文档

| 文档 | 说明 |
|------|------|
| [HTTP-API.md](./HTTP-API.md) | HTTP / Gateway 接口调用 |
| [METHODS.md](./METHODS.md) | Go 方法全表（146+） |
| [COVERAGE.md](./COVERAGE.md) | 服务端 ↔ SDK 覆盖 |
| [Newt-Agent](https://github.com/NewtSpeak/Newt-Agent) | 用户侧 CLI / MCP |
