# NewtBotSdk

NewtSpeak **机器人开放平台官方 SDK**（多语言 monorepo）。  
用 **bot token** 调用 Server 的 `/bot-api/v1`，在 RBAC 权限内实现自动化：消息、反应角色、卡片按钮、治理、语音进房等。

> **bot 即成员**：`User(IsBot=true)` + 角色权限，与人类同一套规则，无特权通道。

```text
你的 Bot 进程  ── NewtBotSdk ──►  https://<server>/bot-api/v1
                              wss://<server>/bot-api/v1/gateway
权限与事件过滤由 Newt-Server 裁决
```

与 [Newt-Agent](https://github.com/NewtSpeak/Newt-Agent) 的区别：Agent 是 **真人 OAuth** 运维/AI 入口；本仓是 **机器人身份** 的程序化 API。

## 语言与包

| 语言 | 目录 | 包名 | 特点 |
|------|------|------|------|
| **JavaScript / TypeScript** | [`javascript/`](javascript/) | `@newtspeak/bot-sdk` | 零依赖；Node ≥ 21（原生 fetch / WebSocket） |
| **Go** | [`go/`](go/) | `github.com/NewtSpeak/NewtBotSdk/go` | Gateway + 可接 pion 语音 |
| **Python** | [`python/`](python/) | `newtspeak-bot` | REST 标准库；Gateway 可选 `websockets` |
| **Rust** | [`rust/`](rust/) | `newtspeak-bot` | `reqwest` + `tokio` + tungstenite |

四语言 API 面 intentionally 对齐：消息（含 ephemeral / 流式 / 按钮交互）、角色、成员治理、邀请、Restriction、语音、贴图、Gateway。

## 能力摘要

| 能力 | 说明 |
|------|------|
| REST | 服/频道/角色/成员/消息/邀请/限制/审计/贴图… |
| Gateway | 与用户端同源事件（按可见性过滤）+ `INTERACTION_CREATE` |
| 卡片按钮 | `custom_id` 交互 + `url` 链接；15 分钟内 callback |
| 流式消息 | 对接 LLM 的打字机输出 |
| ephemeral | 仅指定用户可见 |
| 语音 | `JoinVoice` 取 Media Token，媒体层自接 SFU（参考 loadbot） |
| 上传 | 图标、贴图、附件路径便捷 API |

认证：

```text
Authorization: Bot <newtbot_xxx>
Base:     https://<server>/bot-api/v1
Gateway:  wss://<server>/bot-api/v1/gateway
限流:     约 20 QPS / bot（突发 40）
```

## 快速开始

### 1. 准备 Token

1. 管理控制台 → **开放平台 / 机器人** → 创建  
2. 签发 token（明文仅一次，`newtbot_…`）  
3. 安装到服务器并绑定角色（如 `SEND_MESSAGES`、`MANAGE_ROLES`）

### 2. 安装与最小代码

**JavaScript**

```bash
# monorepo: "@newtspeak/bot-sdk": "file:../NewtBotSdk/javascript"
```

```js
import { OwlBotClient } from "@newtspeak/bot-sdk"
const bot = new OwlBotClient({
  baseUrl: "https://newt-panel.example.com",
  token: process.env.NEWT_BOT_TOKEN,
})
await bot.sendText(channelId, "你好！")
const gw = bot.connectGateway()
gw.on("MESSAGE_CREATE", (msg) => console.log(msg.content))
gw.on("interaction", async (i) => { await i.reply("收到", { ephemeral: true }) })
```

**Go**

```bash
go get github.com/NewtSpeak/NewtBotSdk/go@latest
```

```go
bot := owlbot.New("https://newt-panel.example.com", os.Getenv("NEWT_BOT_TOKEN"))
_, _ = bot.SendText(channelID, "你好！")
gw := bot.ConnectGateway()
gw.OnInteraction(func(i *owlbot.Interaction) { _, _ = i.ReplyText("收到") })
```

**Python**

```bash
pip install -e "./python[gateway]"
```

```python
from newtspeak_bot import OwlBotClient, run_gateway
bot = OwlBotClient("https://newt-panel.example.com", token=os.environ["NEWT_BOT_TOKEN"])
bot.send_message(channel_id, "你好！")
asyncio.run(run_gateway(bot, on_event))
```

**Rust**

```toml
newtspeak-bot = { path = "../NewtBotSdk/rust" }
```

```rust
let bot = Client::new("https://newt-panel.example.com", std::env::var("NEWT_BOT_TOKEN")?)?;
bot.send_text(&channel_id, "你好！").await?;
```

可运行示例：[`examples/`](examples/)（反应角色，四语言）。

## 仓库结构

```text
NewtBotSdk/
├── docs/           # API 协议、覆盖矩阵、Go 方法目录
├── javascript/     # @newtspeak/bot-sdk
├── go/
├── python/
├── rust/
├── examples/       # 最小可运行示例
└── LICENSE         # MIT
```

## 文档

| 文档 | 内容 |
|------|------|
| [**docs/USAGE.md**](docs/USAGE.md) | 使用指南（推荐入口） |
| [**docs/HTTP-API.md**](docs/HTTP-API.md) | 接口调用精简版 |
| [docs/API.md](docs/API.md) | HTTP / Gateway **完整**协议与能力矩阵 |
| [docs/COVERAGE.md](docs/COVERAGE.md) | 服务端挂载 ↔ SDK 覆盖 |
| [docs/METHODS.md](docs/METHODS.md) | Go `Client` 方法全表（146+） |
| [javascript/README.md](javascript/README.md) | JS 专章（流式 AI 示例等） |
| [go/README.md](go/README.md) | Go 专章（语音 / 交互） |
| [python/README.md](python/README.md) | Python 专章 |
| [rust/README.md](rust/README.md) | Rust 专章 |

## 与 Newt-Server

| 仓库 | 职责 |
|------|------|
| **Newt-Server** | 实现 `/bot-api/v1`、权限、Gateway、交互 callback |
| **NewtBotSdk**（本仓） | 官方客户端；**权威源**（独立版本节奏） |

`Newt-Server/sdk/` 若仍存在，仅为兼容镜像。

## 开发自检

```bash
cd go && go test ./... && go build ./...
cd ../python && python -m compileall newtspeak_bot
cd ../rust && cargo check
cd ../javascript && node --check index.js   # Node 21+
```

## 版本与许可

- 当前统一版本：**0.1.0**（随 tag `v0.1.0`）  
- 许可证：[MIT](LICENSE)
