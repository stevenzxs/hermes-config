# 独立 Android 发布身份

- 包名：`com.stevenzxs.hermes_android`；显示名 Ares StevenZXS。
- 基线：上游 v4.0.0；自有开发分支与构建 SHA 见 android-baseline.json。
- RSA 4096 / PKCS12，alias `hermes-release`，证书有效期 10000 天。
- 证书 SHA256：`ccc22121cccab1671afaaa432df4a600c8d2c60dd02dc1f0ce3e812200f14d13`。
- 私钥及凭据保存在仓库外 `D:\hermes-signing`，ACL 仅当前用户和 SYSTEM。密码文件为明文受 ACL 保护，须转存密码管理器；不要上传或共享此目录。
- GitHub 四项 Secrets 仅配置在 hermes-config；源码库不接收私钥，继承的源码 Actions 已停用，避免触发未经审阅的发布。
- 需要用户另做加密离线备份并将密码分开保管；当前目录与 GitHub Secrets 不算离线备份。
- 永久复用此密钥；不得每次构建生成新密钥。丢失密钥将影响普通 APK 原位升级。
- 更新检查及 APK 下载允许列表仅指向 stevenzxs/hermes-android。当前工作流只上传 Actions 制品，不发布 Release；首次没有自有 Release 时更新检查可能返回未找到，不回退上游。
- Kotlin namespace 和进程内 Flutter channel 保持上游值；安装身份、存储沙箱、FileProvider authorities 按独立 applicationId 隔离。
- Play AAB 不在本次交付范围，上游 Play 验证器及继承工作流仍为上游策略，不能作为自有发行入口。
