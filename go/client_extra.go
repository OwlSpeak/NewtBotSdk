package newtbot

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"net/url"
	"path/filepath"
	"strings"
)

// Raw 通用请求：method + path（相对 /bot-api/v1）+ body；out 可为 nil。
// 用于调用尚未单独封装的端点。
func (c *Client) Raw(method, path string, body, out any) error {
	return c.request(method, path, body, out)
}

// ---------- 频道排序 / 解锁 ----------

// ReorderChannels 批量排序频道 body: [{id, position, parent_id?}, ...]
func (c *Client) ReorderChannels(guildID string, entries any) error {
	return c.request("PATCH", "/guilds/"+guildID+"/channels", entries, nil)
}

// UnlockChannel 解锁带密码频道。
func (c *Client) UnlockChannel(channelID, password string) (map[string]any, error) {
	var out map[string]any
	return out, c.request("POST", "/channels/"+channelID+"/unlock",
		map[string]string{"password": password}, &out)
}

// UnlockStatus 频道解锁状态。
func (c *Client) UnlockStatus(channelID string) (map[string]any, error) {
	var out map[string]any
	return out, c.request("GET", "/channels/"+channelID+"/unlock-status", nil, &out)
}

// ReorderRoles 批量排序角色 body: [{id, position}]
func (c *Client) ReorderRoles(guildID string, entries any) error {
	return c.request("PATCH", "/guilds/"+guildID+"/roles", entries, nil)
}

// ---------- 服务器图标 / 横幅 / multi-banner ----------

// UploadGuildIcon 上传服务器图标（multipart 字段 file）。
func (c *Client) UploadGuildIcon(guildID, filename string, data []byte) (map[string]any, error) {
	return c.uploadMultipart("POST", "/guilds/"+guildID+"/icon", filename, data)
}

// DeleteGuildIcon 删除服务器图标。
func (c *Client) DeleteGuildIcon(guildID string) error {
	return c.request("DELETE", "/guilds/"+guildID+"/icon", nil, nil)
}

// UploadGuildBanner 上传服务器横幅。
func (c *Client) UploadGuildBanner(guildID, filename string, data []byte) (map[string]any, error) {
	return c.uploadMultipart("POST", "/guilds/"+guildID+"/banner", filename, data)
}

// DeleteGuildBanner 删除服务器横幅。
func (c *Client) DeleteGuildBanner(guildID string) error {
	return c.request("DELETE", "/guilds/"+guildID+"/banner", nil, nil)
}

// Banners 多 banner 列表。
func (c *Client) Banners(guildID string) (any, error) {
	var out any
	return out, c.request("GET", "/guilds/"+guildID+"/banners", nil, &out)
}

// AddBanner 添加 banner（multipart 或 JSON，视服务端；此处 multipart file）。
func (c *Client) AddBanner(guildID, filename string, data []byte) (map[string]any, error) {
	return c.uploadMultipart("POST", "/guilds/"+guildID+"/banners", filename, data)
}

// ReorderBanners 排序 banners。
func (c *Client) ReorderBanners(guildID string, body any) error {
	return c.request("PATCH", "/guilds/"+guildID+"/banners", body, nil)
}

// RemoveBanner 删除 banner。
func (c *Client) RemoveBanner(guildID, bannerID string) error {
	return c.request("DELETE", "/guilds/"+guildID+"/banners/"+bannerID, nil, nil)
}

// ---------- 成员 name-style / 邀请预览 ----------

// UpdateNameStyle 用户名样式来源角色偏好。
func (c *Client) UpdateNameStyle(guildID, memberID string, body map[string]any) (map[string]any, error) {
	var out map[string]any
	return out, c.request("PATCH", "/guilds/"+guildID+"/members/"+memberID+"/name-style", body, &out)
}

// Invite 邀请码信息（登录预览）。
func (c *Client) Invite(code string) (map[string]any, error) {
	var out map[string]any
	return out, c.request("GET", "/invites/"+code, nil, &out)
}

// PreviewInvite 邀请预览（含公告等）。
func (c *Client) PreviewInvite(code string) (map[string]any, error) {
	var out map[string]any
	return out, c.request("GET", "/invites/"+code+"/preview", nil, &out)
}

// DeleteGuildInvite 按服+码撤销邀请。
func (c *Client) DeleteGuildInvite(guildID, code string) error {
	return c.request("DELETE", "/guilds/"+guildID+"/invites/"+code, nil, nil)
}

// ---------- Restriction 详情/更新 ----------

// Restriction 单条限制详情。
func (c *Client) Restriction(guildID, restrictionID string) (map[string]any, error) {
	var out map[string]any
	return out, c.request("GET", "/guilds/"+guildID+"/restrictions/"+restrictionID, nil, &out)
}

// UpdateRestriction 更新限制。
func (c *Client) UpdateRestriction(guildID, restrictionID string, body map[string]any) (map[string]any, error) {
	var out map[string]any
	return out, c.request("PATCH", "/guilds/"+guildID+"/restrictions/"+restrictionID, body, &out)
}

// ---------- 消息扩展 ----------

// ListEdits 消息编辑历史。
func (c *Client) ListEdits(channelID, messageID string) (any, error) {
	var out any
	return out, c.request("GET", "/channels/"+channelID+"/messages/"+messageID+"/edits", nil, &out)
}

// AckMessage 已读到指定消息。
func (c *Client) AckMessage(channelID, messageID string) error {
	return c.request("POST", "/channels/"+channelID+"/messages/"+messageID+"/ack", map[string]any{}, nil)
}

// AckChannel 频道已读。
func (c *Client) AckChannel(channelID string, body map[string]any) error {
	if body == nil {
		body = map[string]any{}
	}
	return c.request("POST", "/channels/"+channelID+"/ack", body, nil)
}

// AckGuild 全服已读。
func (c *Client) AckGuild(guildID string) error {
	return c.request("POST", "/guilds/"+guildID+"/ack", map[string]any{}, nil)
}

// ReadStates 我的已读状态。
func (c *Client) ReadStates() (any, error) {
	var out any
	return out, c.request("GET", "/users/@me/read-states", nil, &out)
}

// PresignAttachment 附件预签名。
func (c *Client) PresignAttachment(channelID string, body map[string]any) (map[string]any, error) {
	var out map[string]any
	return out, c.request("POST", "/channels/"+channelID+"/attachments/presign", body, &out)
}

// UploadAttachmentContent 上传附件内容（PUT 二进制）。
func (c *Client) UploadAttachmentContent(attachmentID string, contentType string, data []byte) error {
	req, err := http.NewRequest("PUT", c.apiBase+"/attachments/"+attachmentID+"/content", bytes.NewReader(data))
	if err != nil {
		return err
	}
	req.Header.Set("Authorization", "Bot "+c.token)
	if contentType != "" {
		req.Header.Set("Content-Type", contentType)
	}
	resp, err := c.http.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		raw, _ := io.ReadAll(resp.Body)
		return &Error{Status: resp.StatusCode, Message: string(raw)}
	}
	return nil
}

// UploadLimit 服级上传上限。
func (c *Client) UploadLimit(guildID string) (map[string]any, error) {
	var out map[string]any
	return out, c.request("GET", "/guilds/"+guildID+"/upload-limit", nil, &out)
}

// SearchMessages 全系统搜索。
func (c *Client) SearchMessages(query string, guildID, channelID string, limit int) ([]Message, error) {
	params := url.Values{"q": {query}}
	if guildID != "" {
		params.Set("guild_id", guildID)
	}
	if channelID != "" {
		params.Set("channel_id", channelID)
	}
	if limit > 0 {
		params.Set("limit", fmt.Sprint(limit))
	}
	var out struct {
		Messages []Message `json:"messages"`
	}
	return out.Messages, c.request("GET", "/search/messages?"+params.Encode(), nil, &out)
}

// ---------- 入场语音包 ----------

// VoicePacks 列出语音包。
func (c *Client) VoicePacks(guildID string) (any, error) {
	var out any
	return out, c.request("GET", "/guilds/"+guildID+"/voice-packs", nil, &out)
}

// CreateVoicePack 创建语音包。
func (c *Client) CreateVoicePack(guildID string, body map[string]any) (map[string]any, error) {
	var out map[string]any
	return out, c.request("POST", "/guilds/"+guildID+"/voice-packs", body, &out)
}

// PatchVoicePack 更新语音包。
func (c *Client) PatchVoicePack(guildID, packID string, body map[string]any) (map[string]any, error) {
	var out map[string]any
	return out, c.request("PATCH", "/guilds/"+guildID+"/voice-packs/"+packID, body, &out)
}

// DeleteVoicePack 删除语音包。
func (c *Client) DeleteVoicePack(guildID, packID string) error {
	return c.request("DELETE", "/guilds/"+guildID+"/voice-packs/"+packID, nil, nil)
}

// UploadVoicePackAudio 上传语音包音频。
func (c *Client) UploadVoicePackAudio(guildID, packID, filename string, data []byte) (map[string]any, error) {
	return c.uploadMultipart("POST", "/guilds/"+guildID+"/voice-packs/"+packID+"/audio", filename, data)
}

// SelectVoicePack 选用语音包。
func (c *Client) SelectVoicePack(guildID, packID string) error {
	return c.request("PUT", "/guilds/"+guildID+"/voice-packs/"+packID+"/select", map[string]any{}, nil)
}

// MyVoicePack 当前选用。
func (c *Client) MyVoicePack(guildID string) (map[string]any, error) {
	var out map[string]any
	return out, c.request("GET", "/guilds/"+guildID+"/voice-packs/@me", nil, &out)
}

// ClearMyVoicePack 清除选用。
func (c *Client) ClearMyVoicePack(guildID string) error {
	return c.request("DELETE", "/guilds/"+guildID+"/voice-packs/@me", nil, nil)
}

// GuildVoicePackConfig 服级入场语音配置。
func (c *Client) GuildVoicePackConfig(guildID string) (map[string]any, error) {
	var out map[string]any
	return out, c.request("GET", "/guilds/"+guildID+"/voice-pack", nil, &out)
}

// PatchGuildVoicePackConfig 更新服级配置。
func (c *Client) PatchGuildVoicePackConfig(guildID string, body map[string]any) (map[string]any, error) {
	var out map[string]any
	return out, c.request("PATCH", "/guilds/"+guildID+"/voice-pack", body, &out)
}

// ChannelVoicePackConfig 频道入场语音配置。
func (c *Client) ChannelVoicePackConfig(guildID, channelID string) (map[string]any, error) {
	var out map[string]any
	return out, c.request("GET", "/guilds/"+guildID+"/channels/"+channelID+"/voice-pack", nil, &out)
}

// PutChannelVoicePackConfig 更新频道配置。
func (c *Client) PutChannelVoicePackConfig(guildID, channelID string, body map[string]any) (map[string]any, error) {
	var out map[string]any
	return out, c.request("PUT", "/guilds/"+guildID+"/channels/"+channelID+"/voice-pack", body, &out)
}

// ---------- 语音扩展 ----------

// PatchSelfVoiceState 自身静音/闭听。
func (c *Client) PatchSelfVoiceState(guildID string, selfMute, selfDeaf *bool) error {
	body := map[string]any{"guild_id": guildID}
	if selfMute != nil {
		body["self_mute"] = *selfMute
	}
	if selfDeaf != nil {
		body["self_deaf"] = *selfDeaf
	}
	return c.request("PATCH", "/voice/state", body, nil)
}

// VoiceNodes 候选语音节点。
func (c *Client) VoiceNodes(guildID string) (any, error) {
	var out any
	return out, c.request("GET", "/guilds/"+guildID+"/voice/nodes", nil, &out)
}

// VoiceStates 频道语音成员。
func (c *Client) VoiceStates(guildID, channelID string) ([]map[string]any, error) {
	var out struct {
		VoiceStates []map[string]any `json:"voice_states"`
	}
	err := c.request("GET", "/guilds/"+guildID+"/channels/"+channelID+"/voice-states", nil, &out)
	return out.VoiceStates, err
}

// VoicePublicKey Media Token 验签公钥。
func (c *Client) VoicePublicKey() (map[string]any, error) {
	var out map[string]any
	return out, c.request("GET", "/voice/public-key", nil, &out)
}

// ReportVoiceRTT 上报 RTT。
func (c *Client) ReportVoiceRTT(body map[string]any) error {
	return c.request("POST", "/voice/rtt", body, nil)
}

// ReportICEFailed ICE 失败上报。
func (c *Client) ReportICEFailed(body map[string]any) error {
	return c.request("POST", "/voice/ice-failed", body, nil)
}

// AckMigration 迁移确认。
func (c *Client) AckMigration(migrationID string, body map[string]any) error {
	return c.request("POST", "/voice/migrations/"+migrationID+"/ack", body, nil)
}

// ---------- 舞台 / 屏幕共享 ----------

// VoiceStage 舞台配置。
func (c *Client) VoiceStage(channelID string) (map[string]any, error) {
	var out map[string]any
	return out, c.request("GET", "/channels/"+channelID+"/voice-stage", nil, &out)
}

// PatchVoiceStage 更新舞台配置。
func (c *Client) PatchVoiceStage(channelID string, body map[string]any) (map[string]any, error) {
	var out map[string]any
	return out, c.request("PATCH", "/channels/"+channelID+"/voice-stage", body, &out)
}

// StageQueue 申请队列。
func (c *Client) StageQueue(channelID string) (any, error) {
	var out any
	return out, c.request("GET", "/channels/"+channelID+"/stage/queue", nil, &out)
}

// StageRemoveFromQueue 移出队列。
func (c *Client) StageRemoveFromQueue(channelID, userID string) error {
	return c.request("DELETE", "/channels/"+channelID+"/stage/queue/"+userID, nil, nil)
}

// StageApply 申请上麦。
func (c *Client) StageApply(channelID string) error {
	return c.request("POST", "/channels/"+channelID+"/stage/apply", map[string]any{}, nil)
}

// StageCancelApply 取消申请。
func (c *Client) StageCancelApply(channelID string) error {
	return c.request("DELETE", "/channels/"+channelID+"/stage/apply", nil, nil)
}

// StageBringUp 抱上麦。
func (c *Client) StageBringUp(channelID string, body map[string]any) error {
	return c.request("POST", "/channels/"+channelID+"/stage/bring-up", body, nil)
}

// StageBringDown 抱下麦。
func (c *Client) StageBringDown(channelID string, body map[string]any) error {
	return c.request("POST", "/channels/"+channelID+"/stage/bring-down", body, nil)
}

// StageSelfLeave 自行下麦。
func (c *Client) StageSelfLeave(channelID string) error {
	return c.request("POST", "/channels/"+channelID+"/stage/self-leave", map[string]any{}, nil)
}

// ScreenStart 开始屏幕共享。
func (c *Client) ScreenStart(channelID string, body map[string]any) (map[string]any, error) {
	var out map[string]any
	return out, c.request("POST", "/channels/"+channelID+"/voice/screen/start", body, &out)
}

// ScreenStop 结束自己的屏幕共享。
func (c *Client) ScreenStop(channelID string) error {
	return c.request("POST", "/channels/"+channelID+"/voice/screen/stop", map[string]any{}, nil)
}

// ScreenStopUser 强制结束他人屏幕共享。
func (c *Client) ScreenStopUser(channelID string, body map[string]any) error {
	return c.request("POST", "/channels/"+channelID+"/voice/screen/stop-user", body, nil)
}

// ScreenQuota 屏幕共享配额。
func (c *Client) ScreenQuota(guildID string) (map[string]any, error) {
	var out map[string]any
	return out, c.request("GET", "/guilds/"+guildID+"/screen-quota", nil, &out)
}

// ---------- 贴图 ----------

// MyStickerPacks 自建贴图包。
func (c *Client) MyStickerPacks() (any, error) {
	var out any
	return out, c.request("GET", "/users/@me/sticker-packs", nil, &out)
}

// CreateStickerPack 创建贴图包。
func (c *Client) CreateStickerPack(body map[string]any) (map[string]any, error) {
	var out map[string]any
	return out, c.request("POST", "/users/@me/sticker-packs", body, &out)
}

// PatchStickerPack 更新贴图包。
func (c *Client) PatchStickerPack(packID string, body map[string]any) (map[string]any, error) {
	var out map[string]any
	return out, c.request("PATCH", "/users/@me/sticker-packs/"+packID, body, &out)
}

// DeleteStickerPack 软删除贴图包。
func (c *Client) DeleteStickerPack(packID string) error {
	return c.request("DELETE", "/users/@me/sticker-packs/"+packID, nil, nil)
}

// RestoreStickerPack 恢复贴图包。
func (c *Client) RestoreStickerPack(packID string) error {
	return c.request("POST", "/users/@me/sticker-packs/"+packID+"/restore", map[string]any{}, nil)
}

// UploadStickerPackCover 上传封面。
func (c *Client) UploadStickerPackCover(packID, filename string, data []byte) (map[string]any, error) {
	return c.uploadMultipart("PUT", "/users/@me/sticker-packs/"+packID+"/cover", filename, data)
}

// DeleteStickerPackCover 删除封面。
func (c *Client) DeleteStickerPackCover(packID string) error {
	return c.request("DELETE", "/users/@me/sticker-packs/"+packID+"/cover", nil, nil)
}

// UploadStickerItem 上传条目。
func (c *Client) UploadStickerItem(packID, filename string, data []byte) (map[string]any, error) {
	return c.uploadMultipart("POST", "/users/@me/sticker-packs/"+packID+"/items", filename, data)
}

// PatchStickerItem 更新条目。
func (c *Client) PatchStickerItem(packID, itemID string, body map[string]any) (map[string]any, error) {
	var out map[string]any
	return out, c.request("PATCH", "/users/@me/sticker-packs/"+packID+"/items/"+itemID, body, &out)
}

// DeleteStickerItem 删除条目。
func (c *Client) DeleteStickerItem(packID, itemID string) error {
	return c.request("DELETE", "/users/@me/sticker-packs/"+packID+"/items/"+itemID, nil, nil)
}

// CopyStickerItem 复制条目。
func (c *Client) CopyStickerItem(packID string, body map[string]any) (map[string]any, error) {
	var out map[string]any
	return out, c.request("POST", "/users/@me/sticker-packs/"+packID+"/items/copy", body, &out)
}

// StickerLibrary 贴图库。
func (c *Client) StickerLibrary() (any, error) {
	var out any
	return out, c.request("GET", "/users/@me/sticker-library", nil, &out)
}

// InstallStickerPack 安装到库。
func (c *Client) InstallStickerPack(packID string) error {
	return c.request("PUT", "/users/@me/sticker-library/"+packID, map[string]any{}, nil)
}

// UninstallStickerPack 从库移除。
func (c *Client) UninstallStickerPack(packID string) error {
	return c.request("DELETE", "/users/@me/sticker-library/"+packID, nil, nil)
}

// StickerAvailable 可用集合（可选 guild_id）。
func (c *Client) StickerAvailable(guildID string) (any, error) {
	path := "/users/@me/sticker-available"
	if guildID != "" {
		path += "?guild_id=" + url.QueryEscape(guildID)
	}
	var out any
	return out, c.request("GET", path, nil, &out)
}

// StickerPack 包详情。
func (c *Client) StickerPack(packID string) (map[string]any, error) {
	var out map[string]any
	return out, c.request("GET", "/sticker-packs/"+packID, nil, &out)
}

// StickerItem 条目详情。
func (c *Client) StickerItem(itemID string) (map[string]any, error) {
	var out map[string]any
	return out, c.request("GET", "/sticker-items/"+itemID, nil, &out)
}

// StickerPackBans 服 ban 列表。
func (c *Client) StickerPackBans(guildID string) (any, error) {
	var out any
	return out, c.request("GET", "/guilds/"+guildID+"/sticker-pack-bans", nil, &out)
}

// BanStickerPack 服 ban 包。
func (c *Client) BanStickerPack(guildID, packID string) error {
	return c.request("PUT", "/guilds/"+guildID+"/sticker-pack-bans/"+packID, map[string]any{}, nil)
}

// UnbanStickerPack 解除服 ban。
func (c *Client) UnbanStickerPack(guildID, packID string) error {
	return c.request("DELETE", "/guilds/"+guildID+"/sticker-pack-bans/"+packID, nil, nil)
}

// ---------- multipart 辅助 ----------

func (c *Client) uploadMultipart(method, path, filename string, data []byte) (map[string]any, error) {
	var buf bytes.Buffer
	w := multipart.NewWriter(&buf)
	part, err := w.CreateFormFile("file", filepath.Base(filename))
	if err != nil {
		return nil, err
	}
	if _, err := part.Write(data); err != nil {
		return nil, err
	}
	if err := w.Close(); err != nil {
		return nil, err
	}
	req, err := http.NewRequest(method, c.apiBase+path, &buf)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bot "+c.token)
	req.Header.Set("Content-Type", w.FormDataContentType())
	resp, err := c.http.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	raw, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	if resp.StatusCode >= 400 {
		var payload struct {
			Error struct {
				Code    string `json:"code"`
				Message string `json:"message"`
			} `json:"error"`
		}
		_ = json.Unmarshal(raw, &payload)
		return nil, &Error{Status: resp.StatusCode, Code: payload.Error.Code, Message: firstNonEmpty(payload.Error.Message, string(raw))}
	}
	if len(raw) == 0 {
		return map[string]any{}, nil
	}
	var out map[string]any
	if err := json.Unmarshal(raw, &out); err != nil {
		return nil, err
	}
	return out, nil
}

func jsonUnmarshal(data []byte, out any) error {
	return json.Unmarshal(data, out)
}

func firstNonEmpty(values ...string) string {
	for _, v := range values {
		if strings.TrimSpace(v) != "" {
			return v
		}
	}
	return ""
}
