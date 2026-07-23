//! HTTP REST 客户端（异步，基于 reqwest）。

use crate::error::{Error, Result};
use serde::de::DeserializeOwned;
use serde::Serialize;
use serde_json::{json, Value};
use uuid::Uuid;

/// OwlSpeak Bot REST 客户端。
///
/// 认证：`Authorization: Bot <token>`；基础地址自动拼接 `/bot-api/v1`。
#[derive(Clone)]
pub struct Client {
    api_base: String,
    token: String,
    http: reqwest::Client,
}

impl Client {
    /// 创建客户端。`base_url` 形如 `https://owl.example.com`。
    pub fn new(base_url: impl AsRef<str>, token: impl Into<String>) -> Result<Self> {
        let base = base_url.as_ref().trim_end_matches('/');
        if base.is_empty() {
            return Err(Error::Invalid("base_url 不能为空".into()));
        }
        let token = token.into();
        if token.is_empty() {
            return Err(Error::Invalid("token 不能为空".into()));
        }
        let http = reqwest::Client::builder()
            .timeout(std::time::Duration::from_secs(15))
            .build()?;
        Ok(Self {
            api_base: format!("{base}/bot-api/v1"),
            token,
            http,
        })
    }

    /// API 基础地址（含 `/bot-api/v1`），Gateway 会用它推导 `ws(s)://.../gateway`。
    pub fn api_base(&self) -> &str {
        &self.api_base
    }

    /// Bot token 明文。
    pub fn token(&self) -> &str {
        &self.token
    }

    async fn request<T: DeserializeOwned>(
        &self,
        method: reqwest::Method,
        path: &str,
        body: Option<&impl Serialize>,
    ) -> Result<Option<T>> {
        let url = format!("{}{path}", self.api_base);
        let mut builder = self
            .http
            .request(method, &url)
            .header("Authorization", format!("Bot {}", self.token));
        if let Some(body) = body {
            builder = builder
                .header("Content-Type", "application/json")
                .json(body);
        }
        let response = builder.send().await?;
        let status = response.status();
        if status.as_u16() == 204 {
            return Ok(None);
        }
        let text = response.text().await?;
        if !status.is_success() {
            let (code, message) = parse_api_error(&text);
            return Err(Error::api(status.as_u16(), code, message));
        }
        if text.is_empty() {
            return Ok(None);
        }
        Ok(Some(serde_json::from_str(&text)?))
    }

    async fn request_json(
        &self,
        method: reqwest::Method,
        path: &str,
        body: Option<Value>,
    ) -> Result<Value> {
        let url = format!("{}{path}", self.api_base);
        let mut builder = self
            .http
            .request(method, &url)
            .header("Authorization", format!("Bot {}", self.token));
        if let Some(body) = body {
            builder = builder
                .header("Content-Type", "application/json")
                .json(&body);
        }
        let response = builder.send().await?;
        let status = response.status();
        if status.as_u16() == 204 {
            return Ok(Value::Null);
        }
        let text = response.text().await?;
        if !status.is_success() {
            let (code, message) = parse_api_error(&text);
            return Err(Error::api(status.as_u16(), code, message));
        }
        if text.is_empty() {
            return Ok(Value::Null);
        }
        Ok(serde_json::from_str(&text)?)
    }

    // ---------- 基础资源 ----------

    pub async fn me(&self) -> Result<Value> {
        Ok(self
            .request_json(reqwest::Method::GET, "/me", None)
            .await?)
    }

    pub async fn guilds(&self) -> Result<Vec<Value>> {
        let raw = self
            .request_json(reqwest::Method::GET, "/guilds", None)
            .await?;
        Ok(json_array_field(&raw, "guilds"))
    }

    pub async fn guild(&self, guild_id: &str) -> Result<Value> {
        self.request_json(reqwest::Method::GET, &format!("/guilds/{guild_id}"), None)
            .await
    }

    pub async fn update_guild(&self, guild_id: &str, body: Value) -> Result<Value> {
        self.request_json(
            reqwest::Method::PATCH,
            &format!("/guilds/{guild_id}"),
            Some(body),
        )
        .await
    }

    pub async fn channels(&self, guild_id: &str) -> Result<Vec<Value>> {
        let raw = self
            .request_json(
                reqwest::Method::GET,
                &format!("/guilds/{guild_id}/channels"),
                None,
            )
            .await?;
        Ok(json_array_field(&raw, "channels"))
    }

    pub async fn channel(&self, channel_id: &str) -> Result<Value> {
        self.request_json(
            reqwest::Method::GET,
            &format!("/channels/{channel_id}"),
            None,
        )
        .await
    }

    pub async fn create_channel(&self, guild_id: &str, body: Value) -> Result<Value> {
        self.request_json(
            reqwest::Method::POST,
            &format!("/guilds/{guild_id}/channels"),
            Some(body),
        )
        .await
    }

    pub async fn update_channel(&self, channel_id: &str, body: Value) -> Result<Value> {
        self.request_json(
            reqwest::Method::PATCH,
            &format!("/channels/{channel_id}"),
            Some(body),
        )
        .await
    }

    pub async fn delete_channel(&self, channel_id: &str) -> Result<()> {
        let _: Option<Value> = self
            .request(
                reqwest::Method::DELETE,
                &format!("/channels/{channel_id}"),
                None::<&Value>,
            )
            .await?;
        Ok(())
    }

    pub async fn members(&self, guild_id: &str) -> Result<Vec<Value>> {
        let raw = self
            .request_json(
                reqwest::Method::GET,
                &format!("/guilds/{guild_id}/members"),
                None,
            )
            .await?;
        Ok(json_array_field(&raw, "members"))
    }

    pub async fn member(&self, guild_id: &str, member_id: &str) -> Result<Value> {
        self.request_json(
            reqwest::Method::GET,
            &format!("/guilds/{guild_id}/members/{member_id}"),
            None,
        )
        .await
    }

    pub async fn permissions(&self, guild_id: &str) -> Result<Value> {
        self.request_json(
            reqwest::Method::GET,
            &format!("/guilds/{guild_id}/permissions/@me"),
            None,
        )
        .await
    }

    // ---------- 角色 ----------

    pub async fn roles(&self, guild_id: &str) -> Result<Vec<Value>> {
        let raw = self
            .request_json(reqwest::Method::GET, &format!("/guilds/{guild_id}/roles"), None)
            .await?;
        Ok(as_array(raw))
    }

    pub async fn role(&self, guild_id: &str, role_id: &str) -> Result<Value> {
        self.request_json(
            reqwest::Method::GET,
            &format!("/guilds/{guild_id}/roles/{role_id}"),
            None,
        )
        .await
    }

    pub async fn create_role(&self, guild_id: &str, body: Value) -> Result<Value> {
        self.request_json(
            reqwest::Method::POST,
            &format!("/guilds/{guild_id}/roles"),
            Some(body),
        )
        .await
    }

    pub async fn update_role(&self, guild_id: &str, role_id: &str, body: Value) -> Result<Value> {
        self.request_json(
            reqwest::Method::PATCH,
            &format!("/guilds/{guild_id}/roles/{role_id}"),
            Some(body),
        )
        .await
    }

    pub async fn delete_role(&self, guild_id: &str, role_id: &str) -> Result<()> {
        let _: Option<Value> = self
            .request(
                reqwest::Method::DELETE,
                &format!("/guilds/{guild_id}/roles/{role_id}"),
                None::<&Value>,
            )
            .await?;
        Ok(())
    }

    pub async fn add_member_role(
        &self,
        guild_id: &str,
        member_id: &str,
        role_id: &str,
    ) -> Result<Value> {
        self.request_json(
            reqwest::Method::PUT,
            &format!("/guilds/{guild_id}/members/{member_id}/roles/{role_id}"),
            None,
        )
        .await
    }

    pub async fn remove_member_role(
        &self,
        guild_id: &str,
        member_id: &str,
        role_id: &str,
    ) -> Result<()> {
        let _: Option<Value> = self
            .request(
                reqwest::Method::DELETE,
                &format!("/guilds/{guild_id}/members/{member_id}/roles/{role_id}"),
                None::<&Value>,
            )
            .await?;
        Ok(())
    }

    // ---------- 频道覆盖 ----------

    pub async fn overwrites(&self, guild_id: &str, channel_id: &str) -> Result<Vec<Value>> {
        let raw = self
            .request_json(
                reqwest::Method::GET,
                &format!("/guilds/{guild_id}/channels/{channel_id}/overwrites"),
                None,
            )
            .await?;
        Ok(as_array(raw))
    }

    pub async fn set_overwrite(
        &self,
        guild_id: &str,
        channel_id: &str,
        target_id: &str,
        body: Value,
    ) -> Result<Value> {
        self.request_json(
            reqwest::Method::PUT,
            &format!("/guilds/{guild_id}/channels/{channel_id}/overwrites/{target_id}"),
            Some(body),
        )
        .await
    }

    pub async fn delete_overwrite(
        &self,
        guild_id: &str,
        channel_id: &str,
        target_id: &str,
    ) -> Result<()> {
        let _: Option<Value> = self
            .request(
                reqwest::Method::DELETE,
                &format!("/guilds/{guild_id}/channels/{channel_id}/overwrites/{target_id}"),
                None::<&Value>,
            )
            .await?;
        Ok(())
    }

    // ---------- 成员治理 ----------

    pub async fn kick_member(&self, guild_id: &str, member_id: &str) -> Result<()> {
        let _: Option<Value> = self
            .request(
                reqwest::Method::DELETE,
                &format!("/guilds/{guild_id}/members/{member_id}"),
                None::<&Value>,
            )
            .await?;
        Ok(())
    }

    pub async fn leave_guild(&self, guild_id: &str) -> Result<()> {
        self.kick_member(guild_id, "@me").await
    }

    pub async fn update_member(
        &self,
        guild_id: &str,
        member_id: &str,
        body: Value,
    ) -> Result<Value> {
        self.request_json(
            reqwest::Method::PATCH,
            &format!("/guilds/{guild_id}/members/{member_id}"),
            Some(body),
        )
        .await
    }

    pub async fn ban_user(&self, guild_id: &str, user_id: &str, reason: Option<&str>) -> Result<()> {
        let body = match reason {
            Some(r) => json!({ "reason": r }),
            None => json!({}),
        };
        let _: Option<Value> = self
            .request(
                reqwest::Method::PUT,
                &format!("/guilds/{guild_id}/bans/{user_id}"),
                Some(&body),
            )
            .await?;
        Ok(())
    }

    pub async fn unban_user(&self, guild_id: &str, user_id: &str) -> Result<()> {
        let _: Option<Value> = self
            .request(
                reqwest::Method::DELETE,
                &format!("/guilds/{guild_id}/bans/{user_id}"),
                None::<&Value>,
            )
            .await?;
        Ok(())
    }

    pub async fn bans(&self, guild_id: &str) -> Result<Value> {
        self.request_json(reqwest::Method::GET, &format!("/guilds/{guild_id}/bans"), None)
            .await
    }

    pub async fn create_invite(&self, guild_id: &str, body: Value) -> Result<Value> {
        self.request_json(
            reqwest::Method::POST,
            &format!("/guilds/{guild_id}/invites"),
            Some(body),
        )
        .await
    }

    pub async fn invites(&self, guild_id: &str) -> Result<Value> {
        self.request_json(
            reqwest::Method::GET,
            &format!("/guilds/{guild_id}/invites"),
            None,
        )
        .await
    }

    pub async fn delete_invite(&self, code: &str) -> Result<()> {
        let _: Option<Value> = self
            .request(
                reqwest::Method::DELETE,
                &format!("/invites/{code}"),
                None::<&Value>,
            )
            .await?;
        Ok(())
    }

    // ---------- Restriction / 审计 ----------

    pub async fn create_restriction(&self, guild_id: &str, body: Value) -> Result<Value> {
        self.request_json(
            reqwest::Method::POST,
            &format!("/guilds/{guild_id}/restrictions"),
            Some(body),
        )
        .await
    }

    pub async fn restrictions(&self, guild_id: &str) -> Result<Value> {
        self.request_json(
            reqwest::Method::GET,
            &format!("/guilds/{guild_id}/restrictions"),
            None,
        )
        .await
    }

    pub async fn lift_restriction(&self, guild_id: &str, restriction_id: &str) -> Result<()> {
        let _: Option<Value> = self
            .request(
                reqwest::Method::DELETE,
                &format!("/guilds/{guild_id}/restrictions/{restriction_id}"),
                None::<&Value>,
            )
            .await?;
        Ok(())
    }

    pub async fn audit_logs(&self, guild_id: &str) -> Result<Value> {
        self.request_json(
            reqwest::Method::GET,
            &format!("/guilds/{guild_id}/audit-logs"),
            None,
        )
        .await
    }

    // ---------- 消息 ----------

    pub async fn send_message(&self, channel_id: &str, mut body: Value) -> Result<Value> {
        if body.get("nonce").is_none() {
            body["nonce"] = json!(Uuid::new_v4().to_string());
        }
        self.request_json(
            reqwest::Method::POST,
            &format!("/channels/{channel_id}/messages"),
            Some(body),
        )
        .await
    }

    pub async fn send_text(&self, channel_id: &str, content: &str) -> Result<Value> {
        self.send_message(channel_id, json!({ "content": content }))
            .await
    }

    pub async fn send_card(&self, channel_id: &str, card: Value) -> Result<Value> {
        self.send_message(channel_id, json!({ "card": card })).await
    }

    pub async fn get_messages(
        &self,
        channel_id: &str,
        limit: Option<u32>,
        before: Option<&str>,
    ) -> Result<Vec<Value>> {
        let mut params = Vec::new();
        if let Some(limit) = limit {
            params.push(format!("limit={limit}"));
        }
        if let Some(before) = before {
            params.push(format!("before={}", urlencoding::encode(before)));
        }
        let qs = if params.is_empty() {
            String::new()
        } else {
            format!("?{}", params.join("&"))
        };
        let raw = self
            .request_json(
                reqwest::Method::GET,
                &format!("/channels/{channel_id}/messages{qs}"),
                None,
            )
            .await?;
        Ok(json_array_field(&raw, "messages"))
    }

    pub async fn get_message(&self, channel_id: &str, message_id: &str) -> Result<Value> {
        self.request_json(
            reqwest::Method::GET,
            &format!("/channels/{channel_id}/messages/{message_id}"),
            None,
        )
        .await
    }

    pub async fn edit_message(
        &self,
        channel_id: &str,
        message_id: &str,
        content: &str,
    ) -> Result<Value> {
        self.request_json(
            reqwest::Method::PATCH,
            &format!("/channels/{channel_id}/messages/{message_id}"),
            Some(json!({ "content": content })),
        )
        .await
    }

    pub async fn delete_message(&self, channel_id: &str, message_id: &str) -> Result<()> {
        let _: Option<Value> = self
            .request(
                reqwest::Method::DELETE,
                &format!("/channels/{channel_id}/messages/{message_id}"),
                None::<&Value>,
            )
            .await?;
        Ok(())
    }

    pub async fn add_reaction(
        &self,
        channel_id: &str,
        message_id: &str,
        emoji: &str,
    ) -> Result<()> {
        let emoji = urlencoding::encode(emoji);
        let _: Option<Value> = self
            .request(
                reqwest::Method::PUT,
                &format!("/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me"),
                None::<&Value>,
            )
            .await?;
        Ok(())
    }

    pub async fn remove_reaction(
        &self,
        channel_id: &str,
        message_id: &str,
        emoji: &str,
    ) -> Result<()> {
        let emoji = urlencoding::encode(emoji);
        let _: Option<Value> = self
            .request(
                reqwest::Method::DELETE,
                &format!("/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me"),
                None::<&Value>,
            )
            .await?;
        Ok(())
    }

    pub async fn list_reaction_users(
        &self,
        channel_id: &str,
        message_id: &str,
        emoji: &str,
    ) -> Result<Vec<Value>> {
        let emoji = urlencoding::encode(emoji);
        let raw = self
            .request_json(
                reqwest::Method::GET,
                &format!("/channels/{channel_id}/messages/{message_id}/reactions/{emoji}"),
                None,
            )
            .await?;
        Ok(json_array_field(&raw, "users"))
    }

    pub async fn typing(&self, channel_id: &str) -> Result<()> {
        let _: Option<Value> = self
            .request(
                reqwest::Method::POST,
                &format!("/channels/{channel_id}/typing"),
                None::<&Value>,
            )
            .await?;
        Ok(())
    }

    // ---------- 流式消息 ----------

    /// 开始流式消息，返回 `(message_id, 占位消息 JSON)`。
    pub async fn start_stream(
        &self,
        channel_id: &str,
        initial_content: &str,
    ) -> Result<(String, Value)> {
        let msg = self
            .request_json(
                reqwest::Method::POST,
                &format!("/channels/{channel_id}/messages/stream"),
                Some(json!({
                    "content": initial_content,
                    "nonce": Uuid::new_v4().to_string(),
                })),
            )
            .await?;
        let id = msg
            .get("id")
            .and_then(|v| v.as_str())
            .ok_or_else(|| Error::Invalid("流式消息缺少 id".into()))?
            .to_string();
        Ok((id, msg))
    }

    pub async fn stream_append(
        &self,
        channel_id: &str,
        message_id: &str,
        delta: &str,
    ) -> Result<Value> {
        self.request_json(
            reqwest::Method::POST,
            &format!("/channels/{channel_id}/messages/{message_id}/stream"),
            Some(json!({ "delta": delta })),
        )
        .await
    }

    pub async fn stream_end(
        &self,
        channel_id: &str,
        message_id: &str,
        card: Option<Value>,
    ) -> Result<Value> {
        let body = match card {
            Some(card) => json!({ "card": card }),
            None => json!({}),
        };
        self.request_json(
            reqwest::Method::POST,
            &format!("/channels/{channel_id}/messages/{message_id}/stream/end"),
            Some(body),
        )
        .await
    }

    // ---------- 语音 ----------

    pub async fn join_voice(&self, guild_id: &str, channel_id: &str) -> Result<Value> {
        self.request_json(
            reqwest::Method::POST,
            "/voice/join",
            Some(json!({
                "guild_id": guild_id,
                "channel_id": channel_id,
            })),
        )
        .await
    }

    pub async fn leave_voice(&self, guild_id: &str) -> Result<()> {
        let _: Option<Value> = self
            .request(
                reqwest::Method::POST,
                "/voice/leave",
                Some(&json!({ "guild_id": guild_id })),
            )
            .await?;
        Ok(())
    }

    pub async fn refresh_voice_token(&self, guild_id: &str) -> Result<Value> {
        self.request_json(
            reqwest::Method::POST,
            "/voice/refresh-token",
            Some(json!({ "guild_id": guild_id })),
        )
        .await
    }

    pub async fn voice_states(&self, guild_id: &str, channel_id: &str) -> Result<Vec<Value>> {
        let raw = self
            .request_json(
                reqwest::Method::GET,
                &format!("/guilds/{guild_id}/channels/{channel_id}/voice-states"),
                None,
            )
            .await?;
        Ok(json_array_field(&raw, "voice_states"))
    }

    pub async fn voice_disconnect(&self, guild_id: &str, body: Value) -> Result<()> {
        let _: Option<Value> = self
            .request(
                reqwest::Method::POST,
                &format!("/guilds/{guild_id}/voice/disconnect"),
                Some(&body),
            )
            .await?;
        Ok(())
    }

    pub async fn voice_move(&self, guild_id: &str, body: Value) -> Result<()> {
        let _: Option<Value> = self
            .request(
                reqwest::Method::POST,
                &format!("/guilds/{guild_id}/voice/move"),
                Some(&body),
            )
            .await?;
        Ok(())
    }

    pub async fn update_voice_state(
        &self,
        guild_id: &str,
        user_id: &str,
        body: Value,
    ) -> Result<()> {
        let _: Option<Value> = self
            .request(
                reqwest::Method::PATCH,
                &format!("/guilds/{guild_id}/voice/states/{user_id}"),
                Some(&body),
            )
            .await?;
        Ok(())
    }
}

fn parse_api_error(text: &str) -> (String, String) {
    if let Ok(v) = serde_json::from_str::<Value>(text) {
        if let Some(err) = v.get("error") {
            let code = err
                .get("code")
                .and_then(|c| c.as_str())
                .unwrap_or("UNKNOWN")
                .to_string();
            let message = err
                .get("message")
                .and_then(|m| m.as_str())
                .unwrap_or(text)
                .to_string();
            return (code, message);
        }
    }
    ("UNKNOWN".into(), text.to_string())
}

fn json_array_field(value: &Value, field: &str) -> Vec<Value> {
    value
        .get(field)
        .and_then(|v| v.as_array())
        .cloned()
        .unwrap_or_default()
}

fn as_array(value: Value) -> Vec<Value> {
    match value {
        Value::Array(items) => items,
        other => vec![other],
    }
}
