# WSL 构建与 Ubuntu Docker 部署

用户批准：先提交推送、WSL 从固定源码构建、发布 GHCR、服务器拉取部署。无公网开放授权，不改现有 Caddy；不迁移 Windows 密钥和用户数据。

1. 已确认 GHCR 账户镜像清单无 Hermes；Docker Desktop / WSL 引擎可用。
2. 源码基线 v0.23.1 / 3b421578588243f920886e6fe79a6faa87ea026e。git archive 生成干净上下文，调用原生 Dockerfile，不更改产品源码。
3. 配置先提交推送再构建，记录两库 SHA、构建日志、镜像标签及检查结果；镜像不得含真实密钥。
4. 先 --version 检查，再验证网关启动/健康及鉴权，成功才 push；发布后获取 registry digest。不得把本地 image ID 当发布 digest。
5. 部署目录 /opt/stevenzxs-hermes，不覆盖已有目录。Compose bridge 网络，127.0.0.1:8642，数据挂载 ./data，新服务 API Key 单独生成且不输出。
6. 目标 ubuntu@150.158.83.70，仅 sudo -n docker；不修改现有容器、UFW、Caddy，不放入具有推送权限的 registry token。私有镜像拉取凭据另行确认。
7. 验收镜像 digest、服务健康、鉴权、重启稳定性和资源；无模型配置则明确业务调用未验收。

停止条件：认证/空间/资源不足、构建或测试失败、需要变更现有业务、部署位置已占用。D: 构建前至少 40GiB 空间；期间余量不足 20GiB 时停止并审查，不自动清理已有 Docker 数据。

回滚：首次安装失败停止本项目容器并保留 data/log；后续升级保留原 digest 及停机一致性数据备份，回退镜像与相配数据，不执行 down -v。正式部署 Skill 及回滚演练尚待完成。
