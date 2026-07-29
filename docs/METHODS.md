# Go SDK 公开方法目录

模块：`github.com/NewtSpeak/NewtBotSdk/go`（`package newtbot`）

共 **146** 个 `Client` 方法（含文件路径便捷封装）。

生成自源码 `func (c *Client)`；完整 HTTP 语义见 [API.md](./API.md)。

## 基础 / 服务器

- `AddBanner`
- `Banners`
- `DeleteGuildBanner`
- `DeleteGuildIcon`
- `Guild`
- `Guilds`
- `Me`
- `Permissions`
- `RemoveBanner`
- `ReorderBanners`
- `UpdateGuild`
- `UploadGuildBanner`
- `UploadGuildIcon`

## 频道 / 权限

- `Channel`
- `ChannelPermissions`
- `ChannelVoicePackConfig`
- `Channels`
- `CreateChannel`
- `DeleteChannel`
- `DeleteOverwrite`
- `Overwrites`
- `ReorderChannels`
- `SetOverwrite`
- `UnlockChannel`
- `UnlockStatus`
- `UpdateChannel`

## 角色

- `AddMemberRole`
- `CreateRole`
- `DeleteRole`
- `RemoveMemberRole`
- `ReorderRoles`
- `Role`
- `Roles`
- `UpdateRole`

## 成员治理

- `BanStickerPack`
- `BanUser`
- `Bans`
- `KickMember`
- `LeaveGuild`
- `LeaveVoice`
- `Member`
- `Members`
- `UnbanStickerPack`
- `UnbanUser`
- `UpdateMember`
- `UpdateNameStyle`

## 邀请 / Restriction / 审计

- `AuditLogs`
- `CreateInvite`
- `CreateRestriction`
- `DeleteGuildInvite`
- `DeleteInvite`
- `Invite`
- `Invites`
- `LiftRestriction`
- `PreviewInvite`
- `Restriction`
- `Restrictions`
- `UpdateRestriction`

## 消息

- `AckChannel`
- `AckGuild`
- `AckMessage`
- `AddReaction`
- `DeleteMessage`
- `EditMessage`
- `GetMessage`
- `GetMessages`
- `ListEdits`
- `ListReactionUsers`
- `ParseInteraction`
- `PresignAttachment`
- `ReadStates`
- `RemoveReaction`
- `SearchMessages`
- `SendCard`
- `SendEphemeral`
- `SendMessage`
- `SendText`
- `StartStream`
- `Typing`

## 入场语音包

- `ClearMyVoicePack`
- `CreateVoicePack`
- `DeleteVoicePack`
- `GuildVoicePackConfig`
- `MyVoicePack`
- `PatchGuildVoicePackConfig`
- `PatchVoicePack`
- `PutChannelVoicePackConfig`
- `SelectVoicePack`
- `UploadVoicePackAudio`
- `UploadVoicePackAudioFile`
- `VoicePacks`

## 语音

- `AckMigration`
- `JoinVoice`
- `PatchSelfVoiceState`
- `RefreshVoiceToken`
- `ReportICEFailed`
- `ReportVoiceRTT`
- `VoiceDisconnect`
- `VoiceMove`
- `VoiceNodes`
- `VoicePublicKey`
- `VoiceStage`
- `VoiceStates`

## 舞台 / 屏幕

- `PatchVoiceStage`
- `ScreenQuota`
- `ScreenStart`
- `ScreenStop`
- `ScreenStopUser`
- `StageApply`
- `StageBringDown`
- `StageBringUp`
- `StageCancelApply`
- `StageQueue`
- `StageRemoveFromQueue`
- `StageSelfLeave`

## 贴图

- `CopyStickerItem`
- `CreateStickerPack`
- `DeleteStickerItem`
- `DeleteStickerPack`
- `DeleteStickerPackCover`
- `InstallStickerPack`
- `MyStickerPacks`
- `PatchStickerItem`
- `PatchStickerPack`
- `RestoreStickerPack`
- `StickerAvailable`
- `StickerItem`
- `StickerLibrary`
- `StickerPack`
- `StickerPackBans`
- `UninstallStickerPack`
- `UploadStickerItem`
- `UploadStickerItemFile`
- `UploadStickerPackCover`
- `UploadStickerPackCoverFile`

## 文件上传

- `AddBannerFile`
- `UploadAttachmentContent`
- `UploadFile`
- `UploadGuildBannerFile`
- `UploadGuildIconFile`
- `UploadLimit`

## 交互（按钮点击）

`Client` 侧：`ParseInteraction`、`SendEphemeral`（见「消息」）。非 `Client` 方法：

- `Gateway.OnInteraction`（INTERACTION_CREATE → `*Interaction` 包装分发）
- `Interaction.Ack`
- `Interaction.Reply`
- `Interaction.ReplyText`
- `Interaction.UpdateMessage`

## 其它 / Raw

- `ConnectGateway`
- `Raw`
- `UpdateVoiceState`
- `request`
- `uploadMultipart`

