# Hermes 安装与启动配置库

## 边界

- 本仓库：Windows 启动辅助脚本、无密钥模板、部署基线记录。
- 相邻 `../hermes-agent`：官方 Hermes 源码，基线见 `baseline.json`。
- 相邻 `../ares-android`：Ares Android 源码候选基线，见 `android-baseline.json`；接口匹配不等于端到端验证。
- `D:\hermesagent`：现有安装与运行数据。本阶段不移动、不升级、不切换运行程序。
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

## 后续 GitHub Actions（尚未实施）

1. 三个仓库分别使用你自己的 GitHub 远端；不要向官方仓库推送。
2. 代码库负责锁定依赖、测试、构建及发布 CLI / Desktop 产物。
3. 配置库负责配置模板与部署脚本，记录所使用的代码提交 / 发行版本。
4. 构建环境与运行环境分离；真实模型 Key、Android Key 和用户数据不得进入构建产物。
5. 上游自带的 `.github/workflows` 需要在推送到自己的仓库前审阅，不能假定开箱即可打包。

配置库远端：`https://github.com/stevenzxs/hermes-config`。
本仓库目前不包含新增的 Actions 或构建产物。
