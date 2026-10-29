# DRAFT-Bench 开源数据

**Design Reliability Across Feedback and Tasks**：研究通用 Agent 能否在设计任务中落实需求、处理修改与保留要求，并提供可以核验的交付证据。

本仓库由原 Agentic Generation Benchmark 升级，保留仓库地址与历史 VIR 数据。当前为 **v0.2.0 可运行工具包（2026-10-29）**，沿用冻结的 v0.1.0 数据。现已提供任务运行、在线评价与 JSON/CSV 汇总；本次软件发布没有新增实证模型结果或人工标签。

## 本次实际公开的内容

- **Brief Bank：35 个 brief、43 个条件、24 份项目自有输入素材**。包含任务、约束、后续反馈、评分合同与素材哈希。
- **RFQ：40 个场景、100 条运行记录**，其中 99 条有评分、1 条为基础设施排除。开场与评价器答案分开存放，保留可逐条重算的对话及模型标注。
- **全库索引：333 条观测关联、301 个协议单元、272 个 ID／谱系单元**。其中 32 条是历史关联；这些数字既不是完整公开可运行的任务数，也不表示统计独立样本数。
- **R1：7 组历史 Sol/Astra、14 次评价器调用**。不包含 Claude，仍未完成专家最终裁定。

其他历史设计轨道仅公开数值和状态元数据；原始第三方图片、模型生成的设计成品、私有日志与客户原始对话不在本次新数据包中。原有 VIR 数据另行保留。

## 离线检查与任务输入

Python 3.10+，不需要 API key 或额外依赖：

```sh
python3 -m draftbench validate
python3 -m draftbench report
python3 -m draftbench list
python3 -m draftbench prepare design 'DAB-L4-BID-001@zero_shot' --complete --out /tmp/draftbench-bid-input
python3 -m draftbench prepare rfq RFQ-IC-001 --out /tmp/draftbench-rfq-input
```

`validate` 核对文件哈希、输入边界和分母，并从冻结的对话标注重算全部 100 条 RFQ 记录。它验证的是计分复现，不验证模型标注的语义正确性。

`prepare` 导出首轮允许候选看到的内容。候选环境应只挂载导出的目录；整个仓库包含后续反馈和评价答案，不能直接给候选读取。导出工具本身不提供操作系统隔离，也不运行模型。

## 配置 API key，运行并评测

Python 3.10+，macOS/Linux。`prepare --complete` 将交付格式、数量、约束、参考图用途和编辑参数一起放进输入包。

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-eval.txt
cp .env.example .env
# 在本地 .env 中填写 DRAFTBENCH_EVAL_API_KEY（Gemini API key）
python -m draftbench --env-file .env doctor

# 换成实际被测 agent 的适配器命令，使用绝对路径。
AGENT_COMMAND="python /absolute/path/to/your_adapter.py"
python -m draftbench --env-file .env run design 'DAB-L4-BID-001@zero_shot' \
  --agent-command "$AGENT_COMMAND" --out runs/design-one --evaluate
python -m draftbench --env-file .env run rfq RFQ-IC-001 \
  --agent-command "$AGENT_COMMAND" --out runs/rfq-one --evaluate
python -m draftbench summarize --runs runs/design-one --out runs/design-summary
```

**评委 key 与被测 agent 分开配置**：已有运行产物只需要评委 key 就能评分；生成新设计还需要团队自己的 agent、工具与凭证。
提供了可直接连接命令行 agent 的 [通用桥接脚本](examples/command_adapter.py)。
默认评委为 `gemini-3.8-flash`，可通过 `.env` 中的 `DRAFTBENCH_EVAL_MODEL` 固定或更换；每次记录请求、返回值、模型与用量。

先做本地流程检查，无需 API key，以下命令可直接运行：

```sh
python -m draftbench run design 'DAB-L4-BID-001@zero_shot' \
  --agent-command "python $PWD/examples/mock_agent.py" --out runs/plumbing-demo
```

mock 只生成标明用途的占位图，用于测试程序，不代表真实成绩。使用 `run design --all --limit 2` 先跑小批量，
去掉 `--limit` 才运行全部 43 条设计条件；RFQ 全量为 40 场景。批量自动输出 `summary.json` 和 `summary.csv`。
已有运行可用 `evaluate --run runs/design-one --out runs/design-one/evaluation-r2` 再次评分，不需要重跑候选。

设计任务逐轮揭示反馈并保存 v0/v1 等产物快照；RFQ 最多 8 轮客户回复，再独立标注证据并计分。
评委看实际图片/PDF、公开对话与已揭示反馈，不包含内部工具轨迹或私有思考。SVG/HTML 作为源码读取，视觉检查需同时提交 PNG/PDF 预览。
无法验证的维度保留为未知并报告上下界；API 失败、设计超时不会自动变成质量零分。
三个故意缺少必要信息的任务保留缺失状态，以检验澄清行为。完整命令、输入边界、调用上限和输出格式见
[运行指南](docs/RUNNING.md) 和 [适配器协议](docs/ADAPTER.md)。

## 当前证据边界

设计主实验完成率为 Astra 43/43、Claude 35/43，后者八例首轮超时。完成率不等于专业验收率。RFQ 共同 39 例成功数为 36、34；排除原批三个补跑案例后为 33/36、32/36。两批辅助模型和续跑历史不同，不能由此宣布普遍领先。

当前已包含在线多轮运行与暂定的模型评价，但尚未完成专家盲评或验证自动验收准确率。新运行协议的输入、反馈调度与评委可见信息有明确版本，不能与历史成绩直接混合。历史设计成品未随本包公开，不能把分数汇总复算称为独立复现原始评委判断。

详见 [数据卡](DATA_CARD.md)、[协议](docs/PROTOCOL.md)、[复现范围](docs/REPRODUCIBILITY.md)和[历史结果](docs/RESULTS.md)。数据及输入素材沿用 CC BY 4.0；新增 Python 工具采用 MIT。
