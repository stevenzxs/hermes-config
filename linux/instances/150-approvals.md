# 150 Hermes Cron 审批策略

2026-11-24：用户在明确获知“这将修改正常标准流程”、影响当前 Profile 所有 Cron 而非仅一条 sudo 后单独确认，要求同步配置库防止升级丢失。

- 唯一受管非敏感策略：`150-approvals.json`，仅用于 `150.158.83.70` 的 `/opt/data` Profile。
- 保留 `approvals.mode: smart`，设置 `approvals.cron_mode: approve`。不改变 Hermes 产品默认 `deny`，不推广其他实例。
- 允许当前 Profile 的 Cron 自动批准原本需要审批的危险操作，不只是 sudo；不是主机/命令白名单。硬性禁止、目标 Linux 权限和交付/破坏性操作审批约定仍有效。
- 策略配置不授权启动任务、重新构建/占号或执行118升级，不设置 `mode: off` 或全局 YOLO。

## 应用及升级后核验

从已审阅、固定提交的配置库取得 `linux/runtime_approvals.py` 和本目录 JSON，使用运行 Hermes 的虚拟环境 Python（已有 PyYAML）。不要复制完整线上 `config.yaml` 到仓库。

在150容器内、以持有 `/opt/data/config.yaml` 的 hermes 用户执行（工具路径以实际安全暂存目录为准）：

```sh
/opt/hermes/.venv/bin/python runtime_approvals.py --config /opt/data/config.yaml --policy 150-approvals.json
# 默认只读；仅在已明确批准后写入
/opt/hermes/.venv/bin/python runtime_approvals.py --config /opt/data/config.yaml --policy 150-approvals.json --apply
```

工具只替换一个 Cron 值，不重写其他配置或打印秘密；拒绝非 smart 模式、缺字段、重复键及符号链接。写前创建同目录 `config.yaml.before-cron-*` 私有备份，原子替换并读回，保留权限/属主。检查退出0=一致、1=存在差异、2=拒绝。

`linux/compose.yml` 将宿主 `./data` 持久挂载为 `/opt/data`；现有升级器保留 data/runtime.env，不覆盖此配置，所以换镜像不应恢复为默认 deny。升级时保留完整实例 Compose overlay，并对本策略运行上述只读检查；发现漂移先报告，不自动重置整个配置。本次不修改升级器、不自动给其他实例开权限。

Hermes 当前审批实现通过 `load_config_readonly()` 读取配置；须另核验实际部署版本与配置缓存更新路径。磁盘读回及独立 Python 进程的读取，不等同于运行中 Cron/网关已经加载；禁止为了测试而执行真实危险命令。若旧版本需重启，先协调活动会话并取得相应授权，不默认重建容器。

## 回退

仅将 `approvals.cron_mode` 改回 `deny`，保留 `mode: smart`。也可在确认没有后续配置变更后用受限备份恢复；不可用旧全文件覆盖并发修改。核验原生配置读取及下一次安全的审批路径，不重启/删除数据以绕过问题。
