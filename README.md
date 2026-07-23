# OwlBotSdk

OwlSpeak 机器人开放平台 **官方多语言 SDK**  monorepo。

| 语言 | 目录 | 包名 | 依赖特点 |
|------|------|------|----------|
| **JavaScript / TypeScript** | [`javascript/`](javascript/) | `@owlspeak/bot-sdk` | 零依赖，Node ≥ 21 原生 `fetch` + `WebSocket` |
| **Go** | [`go/`](go/) | `github.com/OwlSpeak/OwlBotSdk/go` | `uuid` + `gorilla/websocket` |
| **Python** | [`python/`](python/) | `owlspeak-bot` | REST 标准库；Gateway 可选 `websockets` |
| **Rust** | [`rust/`](rust/) | `owlspeak-bot` | `reqwest` + `tokio` + `tokio-tungstenite` |

文档：

| 文档 | 内容 |
|------|------|
| [`docs/API.md`](docs/API.md) | HTTP / Gateway 协议与能力矩阵 |
| [`docs/COVERAGE.md`](docs/COVERAGE.md) | 服务端挂载 ↔ SDK 覆盖 |
| [`docs/METHODS.md`](docs/METHODS.md) | Go `Client` 公开方法目录（144+） |

---

## 设计原则

1. **bot 即成员**：权限与人类同一套 RBAC，不另开特权通道。  
2. **四语言 API 面一致**：消息、角色、反应角色、成员治理、邀请、Restriction、语音、Gateway。  
3. **与 Discord Bot 能力对齐**（在 OwlSpeak 已实现产品范围内）。  

认证：

```text
Authorization: Bot <owlbot_xxx>
Base URL:     https://<server>/bot-api/v1
Gateway:      wss://<server>/bot-api/v1/gateway
```

---

## 快速开始

### 1. 准备 Token

1. OwlSpeak 管理控制台 → 开放平台 / 机器人 → 创建机器人  
2. 签发 token（明文仅显示一次，形如 `owlbot_…`）  
3. 安装到服务器，并按需绑定角色（如 `MANAGE_ROLES`、`KICK_MEMBERS`）

### 2. 各语言安装

**JavaScript**

```bash
# monorepo 本地
cd javascript && npm link   # 或在业务项目 package.json 中:
# "@owlspeak/bot-sdk": "file:../OwlBotSdk/javascript"
```

```js
import { OwlBotClient } from "@owlspeak/bot-sdk"
const bot = new OwlBotClient({
  baseUrl: "https://owl.example.com",
  token: process.env.OWL_BOT_TOKEN,
})
await bot.sendText(channelId, "你好！")
const gw = bot.connectGateway()
gw.on("MESSAGE_CREATE", (msg) => console.log(msg.content))
```

**Go**

```bash
go get github.com/OwlSpeak/OwlBotSdk/go@latest
# 本地开发：
# go.mod 中 replace github.com/OwlSpeak/OwlBotSdk/go => ../OwlBotSdk/go
```

```go
import owlbot "github.com/OwlSpeak/OwlBotSdk/go"

bot := owlbot.New("https://owl.example.com", os.Getenv("OWL_BOT_TOKEN"))
_, _ = bot.SendText(channelID, "你好！")
gw := bot.ConnectGateway()
gw.On("MESSAGE_CREATE", func(payload json.RawMessage) { /* ... */ })
```

**Python**

```bash
pip install -e "./python[gateway]"
```

```python
from owlspeak_bot import OwlBotClient, run_gateway
import asyncio

bot = OwlBotClient("https://owl.example.com", token=os.environ["OWL_BOT_TOKEN"])
bot.send_message(channel_id, "你好！")

async def on_event(event, data):
    if event == "MESSAGE_CREATE":
        print(data.get("content"))

asyncio.run(run_gateway(bot, on_event))
```

**Rust**

```toml
owlspeak-bot = { path = "../OwlBotSdk/rust" }
tokio = { version = "1", features = ["rt-multi-thread", "macros"] }
```

```rust
use owlspeak_bot::Client;
let bot = Client::new("https://owl.example.com", std::env::var("OWL_BOT_TOKEN")?)?;
bot.send_text("channel-id", "你好！").await?;
```

### 3. 反应角色示例（JS）

```js
const RULES_MESSAGE_ID = process.env.RULES_MESSAGE_ID
const VERIFIED_ROLE_ID = process.env.VERIFIED_ROLE_ID
const gw = bot.connectGateway()
gw.on("MESSAGE_REACTION_ADD", async (ev) => {
  if (String(ev.message_id) !== RULES_MESSAGE_ID || ev.emoji !== "✅") return
  await bot.addMemberRole(ev.guild_id, ev.user_id, VERIFIED_ROLE_ID)
})
```

---

## 仓库结构

```text
OwlBotSdk/
├── README.md                 # 本文件
├── LICENSE                   # MIT
├── docs/API.md               # 完整 HTTP / Gateway 协议
├── javascript/               # @owlspeak/bot-sdk
├── go/                       # github.com/OwlSpeak/OwlBotSdk/go
├── python/                   # owlspeak-bot
├── rust/                     # owlspeak-bot (crates.io 风格)
└── examples/                 # 各语言最小可运行示例
```

---

## 与 Owl-Server 的关系

| 仓库 | 职责 |
|------|------|
| **Owl-Server** | 服务端实现 `/bot-api/v1`、权限、Gateway |
| **OwlBotSdk**（本仓库） | 官方客户端 SDK，独立版本与发布节奏 |

Owl-Server 内若仍保留 `sdk/` 目录，仅作兼容镜像；**以本仓库为权威源**。

---

## 文件上传（路径便捷 API）

```go
// Go
_, err := bot.UploadGuildIconFile(guildID, "./assets/icon.png")
_, err = bot.UploadStickerItemFile(packID, "./stickers/wave.png")
// 通用：bot.UploadFile("POST", "/guilds/"+id+"/icon", "./icon.png")
```

```js
// JavaScript（Node）
await bot.uploadGuildIconFile(guildId, "./assets/icon.png")
await bot.uploadStickerItemFile(packId, "./stickers/wave.png")
// 浏览器：await bot.uploadMultipart("POST", `/guilds/${id}/icon`, fileBlob, "icon.png")
```

```python
# Python
bot.upload_guild_icon_file(guild_id, "./assets/icon.png")
bot.upload_sticker_item_file(pack_id, "./stickers/wave.png")
```

```rust
// Rust
bot.upload_guild_icon_file(guild_id, "./assets/icon.png").await?;
bot.upload_sticker_item_file(pack_id, "./stickers/wave.png").await?;
```

## 开发

```bash
# Go
cd go && go test ./... && go build ./...

# Python
cd python && python -m compileall owlspeak_bot

# Rust
cd rust && cargo check

# JS：语法检查（需 Node 21+）
cd javascript && node --check index.js
```

---

## 版本

当前统一版本：**0.1.0**

变更日志与各语言发布说明随 tag 维护（`v0.1.0`）。

## 许可证

[MIT](LICENSE)
