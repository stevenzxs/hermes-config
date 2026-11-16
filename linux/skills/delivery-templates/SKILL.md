---
name: delivery-templates
description: 列出任务模板并准备需确认的线上交付任务.
version: 1.0.0
author: StevenZXS, Hermes Agent
platforms: [linux]
---

# Delivery Templates Skill

提供Android聊天中的任务菜单与短句入口，不提供原生按钮，不执行默认发布。知识库是唯一规范来源；本Skill仅路由到任务模板和项目已有部署Skill，不另起交付体系。

## When to Use

用户说“列出任务模板”“使用线上交付模板”，或在刚列出的菜单后选择编号1时加载。允许自然语言修改项目、目标及仅构建发布等范围。

## Prerequisites

用 `read_file` 完整读取 /opt/data/workspace/knowledgebase/templates/tasks/online-delivery.md。若不存在，报告模板未同步，不臆造内容或执行。读取知识库README、现行标准及台账，检查Git版本和待合并状态；操作模板不改变规范生效规则。

## How to Run

列表请求只返回：

1. **线上交付** — 默认只读预检，可修改项目、目标和阶段。

示例：`使用线上交付模板，项目 Hermes，目标 115，先预检`。
提示可回复`1，项目 Hermes，目标 115`。列表请求不得执行SSH、构建、发布或部署。

## Quick Reference

- 列表：列出任务模板
- 预检：使用线上交付模板，项目 Hermes，目标 115，先预检
- 调整：使用线上交付模板，项目 Hermes，目标 115，仅构建发布
- 执行：用户对当前预检摘要明确确认后，转入项目已有部署Skill。

## Procedure

用 `read_file` 读取模板，再按模板解析参数。缺省只读预检，修改操作必须等本次摘要确认。用 `terminal` 做必要只读核查；不要输出凭据。
缺少项目Skill、权限或有效规范时报告具体缺口；不能把模板存在当成流水线可用。批准后仍以现行知识库和项目受控入口为准。

## Pitfalls

模板选择不等于发布审批；本Skill不授予永久权限。保护现有CloudMeet及当前Hermes，拒绝自动离线回退。不要在会话中重建系统提示，安装后新建会话。

## Verification

新会话请求“列出任务模板”，确认加载此Skill与知识库模板，返回编号菜单且没有执行操作。预检请求应返回当前参数及阻塞，等待本次确认，不宣称已构建或已部署。
