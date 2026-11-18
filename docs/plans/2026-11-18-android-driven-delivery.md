# Android 对话驱动 Hermes 联合交付 Implementation Plan

**Goal:** Android 对话向150 Hermes提交任务，Hermes修改main、调度配置库Actions发布同版本服务镜像/APK，并部署服务端到115.190.243.21。

**Architecture:** 150为控制端、GitHub Actions为构建发布端、115为运行端。运行秘密与GitHub认证保留150持久化受限目录，不纳入仓库/制品。先实现受控CLI和Skill，再进行真实Android入口验收；本机代跑不能替代。

**Tech Stack:** Python、Git、GitHub CLI、GitHub Actions、Docker、Flutter、SSH。

## Contract

- 允许审阅后的普通main推送；禁止强推、删除数据、升级150控制端或自动安装Android。
- 使用固定三库SHA、GHCR digest、同批发布清单；无本地/目标服务器编译回退。
- 版本待发布前确认；Android versionCode须高于已发布版本并保持既有签名。
- GitHub登录须用户完成，凭据不得打印或借用知识库身份。
- 任一签名、认证、摘要、测试或审批失败均停在对应关口。
- 115默认保留数据与回滚材料；公网入口/TLS和模型凭据另行明确，不复制150秘密。

## Steps and acceptance

1. 预检150、115、工作流及权限（已查：150有git/ssh，无gh；115 SSH root成功，Docker无容器）。
2. 安装固定版本gh到150持久化目录，核验官方摘要；专用GH_CONFIG_DIR，用户设备码授权，检查身份与仓库权限，不输出认证值。
3. 准备150独立源码/配置工作区，读取各仓库AGENTS，配置仓库级提交身份；无覆盖现有非空目录。
4. 测试先行实现linux/delivery/受控编排工具：任务持久化、固定版本及SHA、Actions调度/查询、摘要校验、115部署/回滚；命令重入不重复发布。测试拒绝非预期仓库、主机、漂移SHA及无效digest。
5. 新增配置库联合Actions：手动入口、最小权限、Actions固定SHA、源码固定SHA、服务镜像身份/健康鉴权测试、签名APK原生验证、不可覆盖版本发布、摘要清单和配置包。
6. linux/skills/增加对话交付Skill：明确参数与审批，读取持久化任务查询进度，不以HTTP断开判任务结束，定位已有API审批异常。
7. 分步测试提交推送并部署工具/Skill，禁止重启150工作中控制端；记录安装SHA。
8. 用户从Android发起验收任务：150 Hermes实际调用gh并跟踪最终结果、验证GHCR/APK、SSH115按digest部署；健康/鉴权/持久化/业务/回滚分项留证。
9. 更新知识库唯一台账；缺Android真实入口、业务模型或回滚证据均保留待核验。

## Verification

运行配置库Python聚焦单元测试与git diff --check；云端Actions须取得最终Run URL、三库SHA、制品及摘要。115验证镜像身份、/health、无/错/有效令牌、持久化、容器限额/OOM，公网与业务单独验收。

## Checkpoint

初始阶段：GitHub专用授权未配置，尚无服务镜像Actions。下一步安装gh并进入用户设备码授权；认证阻塞不妨碍本地无秘密工具开发，但禁止调度发布。
