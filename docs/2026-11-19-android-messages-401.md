# Android 加载消息 401：Dashboard 与 Gateway 路由冲突

## 问题及根因

2026-11-19 在150.158.83.70启用 https://hermes.whclaw.top Dashboard 后，Android 加载消息返回 HTTP401，包含 `session_expired`、`invalid_or_expired_session`、`login_url: /login`。

首次代理分流仅将 `/health*`、`/v1/*` 保留给8642 Gateway，其余请求交给9119 Dashboard。但Android会话/消息接口使用 `/api/sessions/{id}/messages`，携带 Gateway Bearer Token，不使用 Dashboard Cookie。误转Dashboard后被网页会话鉴权拒绝。修复前相同Token直连Gateway `/api/sessions` 为200，公网域名为401且报错一致，证明并非API Token失效。此前验收只检查models，遗漏会话/消息路径，未能发现兼容性回归。

## 解决方法

权威配置：`linux/hermes.Caddyfile`。在原分流之前新增 `@gatewayClient`：

- 路径限定 `/api/sessions`、`/api/sessions/*`、`/api/model/options`、`/api/jobs`、`/api/jobs/*`。
- 同时要求 `Authorization: Bearer *`，匹配时转发8642；该匹配仅选后端，不代表认证通过，Token仍由Gateway校验。
- 不带Bearer的浏览器Cookie请求仍走Dashboard9119；其他Dashboard管理API不泛化转发。
- 保留原 `/health*`、`/v1/*` Gateway路由；不修改密码、API Token、Android数据或全局认证，不增加Caddy Basic Auth。

适用镜像源码：`3b421578588243f920886e6fe79a6faa87ea026e`。本次仅更新现有Caddy的Hermes站点块，validate通过后reload，无镜像构建/发布，无Hermes容器重启。用户授权修复及归档，沿用本次配置变更限定例外，不关闭其他交付整改。

## 验收（严格HTTPS，未输出会话内容/凭据）

| 检查 | 修复后 |
|---|---|
| 现有Token GET /api/sessions | 200 |
| 现有真实会话 GET /api/sessions/{id}/messages | 200 |
| sessions、model/options、jobs错误Token | 均401 |
| sessions、model/options、jobs正确Token | 均200 |
| 无凭据 /api/sessions | 401 |
| Dashboard原生登录及Cookie /api/config | 均200 |
| Dashboard Cookie /api/sessions | 200 |
| /health、正确Token /v1/models | 均200 |

以上为HTTP/API回归。用户随后确认Android手机端已恢复正常，补齐本次加载消息问题的真机确认；未据此扩大为发消息/流式聊天或完整浏览器交互验收。无需重新安装或清理数据。

## 回滚和预防

远端备份：`/home/ubuntu/caddy-deploy/Caddyfile.before-android-api-20261119T025822Z`。回滚只恢复本次Hermes站点块，避免覆盖其后其他站点修改；validate后reload。未执行回滚演练。注意回滚会重新引入Android消息401。

未来同域名增加Dashboard或改代理，必须同时回归Android会话列表/真实消息读取、错误Token拒绝，以及Dashboard Cookie路径，不能仅凭health/models通过声称兼容。若新增共享接口，先查明后端契约及认证方式，再扩充精确路径白名单；不要将全部 `/api/*` 无条件转给某一个后端。
