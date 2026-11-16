# Hermes 安装与启动配置库

## 边界

- 本仓库：受控 GitHub Actions、Windows 启动和数据恢复脚本、Android 签名准备入口、无密钥模板及部署基线记录。
- 相邻 `../hermes-agent`：官方 Hermes 源码，基线见 `baseline.json`。
- 相邻 `../ares-android`：Ares Android 源码候选基线，见 `android-baseline.json`；接口匹配不等于端到端验证。
- `D:\hermesagent`：已安装的云端 Windows 产物与运行数据；旧安装备份在 `D:\hermesagent-old`。
- 三个目录分别作为独立 Git 仓库管理，父目录不建立 Git 仓库。

## 当前脚本

`windows/` 保存现有安装目录中人工维护的启动脚本快照，不包含安装器、日志、密钥或数据库。
脚本仍以 `D:\hermesagent` 为运行根目录，Android 辅助脚本中的地址也仍为当前机器地址。
不要直接在源码目录里试运行这些脚本：它们会操作现有安装；`connect-android.cmd` 会重启运行网关。
实际部署时应审阅后成套复制到安装根目录，源代码目录并不是运行数据目录。

## 保密

不提交真实 `home/config.yaml`、`.env`、认证状态、用户会话、记忆、缓存或已打包二进制。
`templates/.env.example` 仅列举占位符，不能直接用来覆盖已有 `.env`。
此前对工具目录 ACL 和 Windows 防火墙的调整不是代码文件，不会随这些脚本自动迁移。
API 服务的监听设置需要部署阶段单独配置；复制启动脚本不等于启用手机连接。

## GitHub Actions 交付入口

1. 三个仓库分别使用你自己的 GitHub 远端；不要向官方仓库推送。
2. 代码库负责产品源码、依赖锁、测试及原生编译入口。
3. 配置库负责实际使用的工作流、打包安装与部署编排，记录代码 / 配置提交和产物摘要。
4. 构建环境与运行环境分离；真实模型 Key、Android Key 和用户数据不得进入构建产物。
5. 上游自带的 `.github/workflows` 需要在推送到自己的仓库前审阅，不能假定开箱即可打包。

配置库远端：`https://github.com/stevenzxs/hermes-config`。
Windows：`.github/workflows/hermes-windows.yml`，Run 43792138239 已成功并完成下载摘要及本机最小启动验证。未签名 commit build，显示版本 0.0.0；并非正式签名发行。

Android：`.github/workflows/hermes-android.yml`，手动触发，固定 `android-baseline.json` 对应源码 v4.0.0 / 6a880cdb5531255501c6c237eb6909c5bc13c57c，Flutter 3.44.0、Java 17。调用原生 Flutter 构建和 `scripts/verify_release_apks.py`，产出三个 ABI 的正式签名 APK、SHA256SUMS 和源码/配置 SHA 记录，不自动发布 GitHub Release / Play，也不自动部署手机。

### Android 正式签名前置条件（当前阻塞）

在配置库 GitHub Actions Secrets 中由密钥持有人安全配置 `KEYSTORE_BASE64`、`STORE_PASSWORD`、`KEY_PASSWORD`、`KEY_ALIAS`。不得在聊天、仓库文件或日志中提交值。当前核验配置库和 Android 仓库均无仓库级 Secrets、无 Environment。

入口必须验证证书 SHA256 为源码正式身份 `475baf431b16d050c8f658ac838783b273f7c10bba06ed1d16bb0a4239f592fb`；缺少密钥或身份不符直接失败，不回退 Debug、不生成新密钥替代。该摘要不代表已拥有上游私钥的使用授权。若需要自有签名身份，必须单独批准应用升级/包名及原生验签策略变更，本入口不会绕过。

Windows 与 Android 是独立手动工作流；没有自动联动或 `all` 总编排。配置包工作流、部署 Skill 和项目族聚合门禁尚未实现，不把单项成功称为项目族完成。

## Windows D 盘交付改造（进行中）

- 执行计划：`docs/plans/2026-11-16-windows-d-drive.md`。
- `windows/build-hermes.ps1` 从 `baseline.json` 校验相邻源码 HEAD 与干净状态，调用产品原生 bundled 构建入口，传入 `--dir --publish never`。
- 默认构建目录 `D:\hermes-build`，与正式安装目录、备份和用户数据分离；不修改全局环境变量。
- 运行 `windows/test-build-preflight.ps1` 验证构建目录不能落在 C 盘、正式安装目录或备份目录。
- 构建脚本成功不代表安装或健康检查成功；构建失败时不得改用旧二进制冒充新产物。
- 旧安装已由用户迁移到 `D:\hermesagent-old`，后续保留该备份，新安装目标为 `D:\hermesagent`。上文“不移动”描述的是初始化阶段，不再表示当前安装状态。
- 源码远端 main/tag 已核验；Windows 云端构建与最小安装验收已完成。Android 正式签名云端构建待授权凭据，尚无成功 Run / APK 证据。
