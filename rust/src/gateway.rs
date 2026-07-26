//! Gateway 实时事件：HELLO / IDENTIFY / HEARTBEAT，断线指数退避重连。

use crate::client::Client;
use crate::error::{Error, Result};
use crate::interaction::Interaction;
use futures_util::{SinkExt, StreamExt};
use serde_json::Value;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::{mpsc, Mutex};
use tokio_tungstenite::{connect_async, tungstenite::Message};

/// 事件回调：`(事件名, 载荷 JSON)`。内置事件 `"READY"` 表示连接就绪。
pub type EventHandler = Arc<dyn Fn(String, Value) + Send + Sync + 'static>;

/// Gateway 连接句柄。
pub struct Gateway {
    stop_tx: mpsc::Sender<()>,
    join: tokio::task::JoinHandle<()>,
}

impl Gateway {
    /// 关闭连接并停止重连。
    pub async fn close(self) {
        let _ = self.stop_tx.send(()).await;
        let _ = self.join.await;
    }
}

/// 线程安全的事件处理表。
#[derive(Default, Clone)]
pub struct HandlerMap {
    inner: Arc<Mutex<HashMap<String, Vec<EventHandler>>>>,
}

impl HandlerMap {
    pub fn new() -> Self {
        Self::default()
    }

    /// 注册事件回调（如 `MESSAGE_CREATE` / `MESSAGE_REACTION_ADD` / `READY`）。
    pub async fn on<F>(&self, event: impl Into<String>, handler: F)
    where
        F: Fn(String, Value) + Send + Sync + 'static,
    {
        let mut map = self.inner.lock().await;
        map.entry(event.into())
            .or_default()
            .push(Arc::new(handler));
    }

    /// 注册按钮点击回调：`INTERACTION_CREATE` 载荷自动包装成 [`Interaction`]。
    ///
    /// 需要传入 `Client`（用于回应 callback 端点）；解析失败的载荷会被忽略。
    pub async fn on_interaction<F>(&self, client: Client, handler: F)
    where
        F: Fn(Interaction) + Send + Sync + 'static,
    {
        self.on("INTERACTION_CREATE", move |_, payload| {
            if let Ok(interaction) = Interaction::from_value(client.clone(), payload) {
                handler(interaction);
            }
        })
        .await;
    }

    async fn emit(&self, event: &str, payload: Value) {
        let handlers = {
            let map = self.inner.lock().await;
            map.get(event).cloned().unwrap_or_default()
        };
        for h in handlers {
            h(event.to_string(), payload.clone());
        }
    }
}

/// 连接 Gateway 并开始分发事件。
pub async fn connect(client: Client, handlers: HandlerMap) -> Result<Gateway> {
    let (stop_tx, mut stop_rx) = mpsc::channel::<()>(1);
    let handlers = Arc::new(handlers);
    let client = Arc::new(client);

    let join = tokio::spawn(async move {
        let mut backoff_ms: u64 = 1000;
        loop {
            tokio::select! {
                _ = stop_rx.recv() => break,
                result = run_session(client.clone(), handlers.clone()) => {
                    match result {
                        Ok(true) => backoff_ms = 1000,
                        Ok(false) | Err(_) => {}
                    }
                }
            }
            tokio::select! {
                _ = stop_rx.recv() => break,
                _ = tokio::time::sleep(std::time::Duration::from_millis(backoff_ms)) => {
                    backoff_ms = (backoff_ms * 2).min(30_000);
                }
            }
        }
    });

    Ok(Gateway { stop_tx, join })
}

async fn run_session(client: Arc<Client>, handlers: Arc<HandlerMap>) -> Result<bool> {
    let ws_url = gateway_url(client.api_base());
    let (ws, _) = connect_async(&ws_url)
        .await
        .map_err(|e| Error::WebSocket(e.to_string()))?;
    let (write, mut read) = ws.split();
    let write = Arc::new(Mutex::new(write));

    let mut ready = false;
    let mut heartbeat_task: Option<tokio::task::JoinHandle<()>> = None;

    while let Some(msg) = read.next().await {
        let msg = msg.map_err(|e| Error::WebSocket(e.to_string()))?;
        let text = match msg {
            Message::Text(t) => t.to_string(),
            Message::Binary(b) => String::from_utf8_lossy(&b).into_owned(),
            Message::Close(_) => break,
            Message::Ping(p) => {
                let mut w = write.lock().await;
                let _ = w.send(Message::Pong(p)).await;
                continue;
            }
            _ => continue,
        };
        let frame: Value = match serde_json::from_str(&text) {
            Ok(v) => v,
            Err(_) => continue,
        };
        let op = frame.get("op").and_then(|v| v.as_str()).unwrap_or("");
        match op {
            "HELLO" => {
                let identify = serde_json::json!({
                    "op": "IDENTIFY",
                    "d": { "token": client.token() }
                });
                {
                    let mut w = write.lock().await;
                    w.send(Message::Text(identify.to_string().into()))
                        .await
                        .map_err(|e| Error::WebSocket(e.to_string()))?;
                }
                let interval_ms = frame
                    .get("d")
                    .and_then(|d| d.get("heartbeat_interval_ms"))
                    .and_then(|v| v.as_u64())
                    .unwrap_or(30_000);
                if let Some(task) = heartbeat_task.take() {
                    task.abort();
                }
                let write_hb = write.clone();
                heartbeat_task = Some(tokio::spawn(async move {
                    let mut ticker =
                        tokio::time::interval(std::time::Duration::from_millis(interval_ms));
                    // 跳过第一次立即触发
                    ticker.tick().await;
                    loop {
                        ticker.tick().await;
                        let beat = Message::Text(
                            serde_json::json!({ "op": "HEARTBEAT" }).to_string().into(),
                        );
                        let mut w = write_hb.lock().await;
                        if w.send(beat).await.is_err() {
                            break;
                        }
                    }
                }));
            }
            "READY" => {
                ready = true;
                let d = frame.get("d").cloned().unwrap_or(Value::Null);
                handlers.emit("READY", d).await;
            }
            "DISPATCH" => {
                let t = frame
                    .get("t")
                    .and_then(|v| v.as_str())
                    .unwrap_or("")
                    .to_string();
                let d = frame.get("d").cloned().unwrap_or(Value::Null);
                if !t.is_empty() {
                    handlers.emit(&t, d).await;
                }
            }
            "HEARTBEAT_ACK" => {}
            _ => {}
        }
    }

    if let Some(task) = heartbeat_task {
        task.abort();
    }
    Ok(ready)
}

fn gateway_url(api_base: &str) -> String {
    let base = if let Some(rest) = api_base.strip_prefix("https://") {
        format!("wss://{rest}")
    } else if let Some(rest) = api_base.strip_prefix("http://") {
        format!("ws://{rest}")
    } else {
        api_base.to_string()
    };
    format!("{base}/gateway")
}
