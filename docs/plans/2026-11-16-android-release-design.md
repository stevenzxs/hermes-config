# Android 正式 Release 打包修复

用户批准：补齐 Android 打包，不修改知识库防漏机制，不增加项目族总编排；明确选择正式签名 Release，不允许 Debug 替代。

## 设计和执行计划

1. 配置库拥有单独 workflow_dispatch 入口；固定 Android v4.0.0 SHA，调用 Flutter 原生构建，不修改产品源码。
2. 四项 GitHub Secrets 仅在签名准备步骤注入，私钥落在临时 Runner，key.properties 不进入制品，always 步骤清除；先验证授权证书，缺项即停。
3. 锁文件解析、原生验签脚本测试、Flutter analyze/test 先于 APK 构建，失败停止。
4. 原生 verify_release_apks 校验三个 ABI、包名、版本码、正式证书和包内来源资产，再生成摘要和 SHA 配对记录上传。
5. 只提交本次 Android 入口、测试和修正说明；保留已有 Windows 部署未提交改动。运行本地轻量测试和 YAML 校验，不本地构建 APK。

## 当前阻塞

GitHub API 核验：个人所有者 stevenzxs，两个仓库仓库级 Secrets 均为空、Environment 均为空。无授权私钥，不触发注定失败的正式构建、不生成替代密钥、不降低验签要求。

## 验收边界

本轮可验收配置实现、缺凭据/错误证书的 fail-closed 行为；实际 APK 构建、签名、下载和手机/后端联调均未验收。知识库规则及其防漏机制保持不变。
