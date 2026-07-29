//! SDK 统一错误类型。

use thiserror::Error;

/// NewtSpeak Bot API 错误。
#[derive(Debug, Error)]
pub enum Error {
    /// HTTP 业务错误（服务端返回 4xx/5xx 且带 error.code）。
    #[error("{message} ({code}, HTTP {status})")]
    Api {
        status: u16,
        code: String,
        message: String,
    },
    /// HTTP 传输层错误。
    #[error("HTTP 请求失败: {0}")]
    Http(#[from] reqwest::Error),
    /// JSON 编解码错误。
    #[error("JSON 错误: {0}")]
    Json(#[from] serde_json::Error),
    /// WebSocket 错误。
    #[error("WebSocket 错误: {0}")]
    WebSocket(String),
    /// 参数或状态非法。
    #[error("{0}")]
    Invalid(String),
}

impl Error {
    pub fn api(status: u16, code: impl Into<String>, message: impl Into<String>) -> Self {
        Self::Api {
            status,
            code: code.into(),
            message: message.into(),
        }
    }
}

pub type Result<T> = std::result::Result<T, Error>;
