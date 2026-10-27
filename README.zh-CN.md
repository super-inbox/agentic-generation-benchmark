# DRAFT-Bench 开源数据

**Design Reliability Across Feedback and Tasks**：研究通用 Agent 能否在设计任务中落实需求、处理修改与保留要求，并提供可以核验的交付证据。

本仓库由原 Agentic Generation Benchmark 升级，保留仓库地址与历史 VIR 数据。当前为 **v0.1.0 数据发布版（2026-10-26）**，对应 2026-10-24 论文使用的归档证据，本次发布没有新增模型实验或人工标签。

## 本次实际公开的内容

- **Brief Bank：35 个 brief、43 个条件、24 份项目自有输入素材**。包含任务、约束、后续反馈、评分合同与素材哈希。
- **RFQ：40 个场景、100 条运行记录**，其中 99 条有评分、1 条为基础设施排除。开场与评价器答案分开存放，保留可逐条重算的对话及模型标注。
- **全库索引：333 条观测关联、301 个协议单元、272 个 ID／谱系单元**。其中 32 条是历史关联；这些数字既不是完整公开可运行的任务数，也不表示统计独立样本数。
- **R1：7 组历史 Sol/Astra、14 次评价器调用**。不包含 Claude，仍未完成专家最终裁定。

其他历史设计轨道仅公开数值和状态元数据；原始第三方图片、模型生成的设计成品、私有日志与客户原始对话不在本次新数据包中。原有 VIR 数据另行保留。

## 使用

Python 3.10+，不需要 API key 或额外依赖：

```sh
python3 -m draftbench validate
python3 -m draftbench report
python3 -m unittest discover -s tests -v
python3 -m draftbench prepare design 'DAB-L4-BID-001@zero_shot' --out /tmp/draftbench-bid-input
python3 -m draftbench prepare rfq RFQ-IC-001 --out /tmp/draftbench-rfq-input
```

`validate` 核对文件哈希、输入边界和分母，并从冻结的对话标注重算全部 100 条 RFQ 记录。它验证的是计分复现，不验证模型标注的语义正确性。

`prepare` 导出首轮允许候选看到的内容。候选环境应只挂载导出的目录；整个仓库包含后续反馈和评价答案，不能直接给候选读取。导出工具本身不提供操作系统隔离，也不运行模型。

## 当前证据边界

设计主实验完成率为 Astra 43/43、Claude 35/43，后者八例首轮超时。完成率不等于专业验收率。RFQ 共同 39 例成功数为 36、34；排除原批三个补跑案例后为 33/36、32/36。两批辅助模型和续跑历史不同，不能由此宣布普遍领先。

当前能完成数据检查、RFQ 历史计分复现和候选输入准备。完整在线多轮执行器、设计语义自动验收、专家盲评仍需后续补齐。设计成品未随本包公开，不能把历史设计分数汇总复算称为独立复现原始评委判断。

详见 [数据卡](DATA_CARD.md)、[协议](docs/PROTOCOL.md)、[复现范围](docs/REPRODUCIBILITY.md)和[历史结果](docs/RESULTS.md)。数据及输入素材沿用 CC BY 4.0；新增 Python 工具采用 MIT。
