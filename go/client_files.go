package owlbot

import (
	"os"
	"path/filepath"
)

// readUploadFile 读取本地文件，返回 basename 与内容。
func readUploadFile(path string) (filename string, data []byte, err error) {
	data, err = os.ReadFile(path)
	if err != nil {
		return "", nil, err
	}
	return filepath.Base(path), data, nil
}

// UploadGuildIconFile 从本地路径上传服务器图标。
func (c *Client) UploadGuildIconFile(guildID, path string) (map[string]any, error) {
	name, data, err := readUploadFile(path)
	if err != nil {
		return nil, err
	}
	return c.UploadGuildIcon(guildID, name, data)
}

// UploadGuildBannerFile 从本地路径上传服务器横幅。
func (c *Client) UploadGuildBannerFile(guildID, path string) (map[string]any, error) {
	name, data, err := readUploadFile(path)
	if err != nil {
		return nil, err
	}
	return c.UploadGuildBanner(guildID, name, data)
}

// AddBannerFile 从本地路径添加 multi-banner。
func (c *Client) AddBannerFile(guildID, path string) (map[string]any, error) {
	name, data, err := readUploadFile(path)
	if err != nil {
		return nil, err
	}
	return c.AddBanner(guildID, name, data)
}

// UploadVoicePackAudioFile 从本地路径上传入场语音包音频。
func (c *Client) UploadVoicePackAudioFile(guildID, packID, path string) (map[string]any, error) {
	name, data, err := readUploadFile(path)
	if err != nil {
		return nil, err
	}
	return c.UploadVoicePackAudio(guildID, packID, name, data)
}

// UploadStickerPackCoverFile 从本地路径上传贴图包封面。
func (c *Client) UploadStickerPackCoverFile(packID, path string) (map[string]any, error) {
	name, data, err := readUploadFile(path)
	if err != nil {
		return nil, err
	}
	return c.UploadStickerPackCover(packID, name, data)
}

// UploadStickerItemFile 从本地路径上传贴图条目。
func (c *Client) UploadStickerItemFile(packID, path string) (map[string]any, error) {
	name, data, err := readUploadFile(path)
	if err != nil {
		return nil, err
	}
	return c.UploadStickerItem(packID, name, data)
}

// UploadFile 通用：multipart 字段 file，从本地路径上传到任意 bot-api 路径。
// path 为 API 路径（如 /guilds/{id}/icon），filePath 为本地文件。
func (c *Client) UploadFile(method, apiPath, filePath string) (map[string]any, error) {
	name, data, err := readUploadFile(filePath)
	if err != nil {
		return nil, err
	}
	return c.uploadMultipart(method, apiPath, name, data)
}
