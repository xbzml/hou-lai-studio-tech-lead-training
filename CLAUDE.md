# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 这个仓库是什么

HOULAI 技术负责人训练营（V1）的**合成训练包**，不是生产代码库，也不是真实客户项目的缺陷报告。唯一实际代码是 `学员资料/训练项目/` 下的 Python 标准库练习项目 **OrderCheck Lab**，由学员小陈按关卡 T01–T04 逐步实现。根目录当前不是 Git 仓库；练习仓库按需在 `学员资料/训练项目/` 里 `git init`。

不可逾越的边界：
- 训练代码不得部署生产、不得推送到正式 GitHub 仓库（`Pure-Heart-web/order-guard`、`houlai-fde` 仅供 T00 只读对照）。
- 只用合成数据，不处理真实客户文件、不联网、不申请 API Key。
- `创始人专用/` 存放评分标准、事件注入卡和**隐藏探针** `test_t02.py`、`test_t03.py`。探针不得提前给学员看；不得为了让探针通过而修改探针、写死样本或改动预期。
- 正式工程迁移以真实仓库最新 Issue 和 FDE Gate 0 PASS 为前提，本训练包不能替代。

## 常用命令

均在 `学员资料/训练项目/` 下执行（Python 3.10+，无第三方依赖、无 lint/CI 配置）：

```bash
python -m unittest discover -s tests -v          # 公开冒烟测试（3 项，当前 OK）
python -m unittest tests.test_smoke.Smoke.test_normal -v   # 运行单个测试
python -m ordercheck fixtures/order_ok.txt       # JSON 输出；PASS 退出码 0
python -m ordercheck fixtures/order_missing.txt  # 当前仍为 PASS（starter 未检查 Material）
```

导师探针（必须在学员工作区根目录、确认可导入实际 `ordercheck` 后运行；结果不得泄露给学员）：

```bash
python -m unittest discover -s ../../创始人专用 -p 'test_t02.py' -v
python -m unittest discover -s ../../创始人专用 -p 'test_t03.py' -v
```

当前基线（刻意保留）：公开冒烟 3 项 OK；T02 探针 6 个失败；T03 探针 29 失败 + 3 错误。这些失败是训练起点，不是待自动修复的缺陷。

## 架构与契约

- `ordercheck/__main__.py`：CLI 适配层，读文件 → `check_order` → 输出 JSON → 按 decision 映射退出码（PASS 0 / REVIEW 1 / BLOCK 2）。T03 要求所有读取失败、非 UTF-8、非 TXT、执行异常都 fail closed 返回 BLOCK。
- `ordercheck/checker.py`：领域规则层，纯函数 `check_order(text) -> {'decision', 'findings'}`，findings 每项含 `field` 与 `code`。T02 只做必填与占位符检查（MISSING_FIELD）；T03 才扩展重复/未知键、不可解析行、数值有限性、单位、枚举值等严格校验。
- `ordercheck/evidence.py`：**领域无关**的证据核验内核，按 UTF-8 字节半开区间定位并绑定 SHA-256：`make_pointer(document_id, raw, start, end)` 与 `verify_pointer(document_id, raw, pointer) -> VERIFIED / REJECTED / UNVERIFIABLE`。T04 要求把它提取为独立可安装包，供订单与合同（`fixtures/contract.txt`、`handover.txt`）两个场景消费；Core 里不能出现 Order ID、Quantity、交付物等业务字段。
- `tests/test_smoke.py`：公开冒烟，仅覆盖正常样本、缺 Quantity、简单 pointer，**不等于验收**。`fixtures/` 全部为合成数据。
- `SPEC.md` 是唯一验收契约（业务边界、T02/T03/T04 要求、CLI 退出码、pointer 语义）；`README.md` 说明实验边界。starter 故意不完整，任何"公开测试通过"都不能宣称验收或生产安全。

starter 的已知缺口（继续训练时应由学员按关卡修复，而非一次性补全）：只检查 6 个字段（漏 Material）、不识别 `TBD/待定` 占位符、解析时静默丢弃无冒号行并接受重复/未知键、CLI 未捕获异常、`verify_pointer` 只判断 quote 是否出现在 raw 中、`make_pointer` 无边界校验。

## 工作方式

- 先读 `学员资料/00_开始训练.md`、当前关卡卡和 `SPEC.md`；与学员协作时遵循 `01_AI工程驾驶手册.md` 与 `02_AI命令库.md`（P00–P13）的角色与边界。默认假设是"学员掌握方向盘"，不是由 AI 代跑全流程。
- 按关卡推进，不擅自跨关：T02 不提前实现 T03 的安全机制或 T04 的打包；若用户要求整体完成，先确认目标关卡与验收范围。
- 先冻结预期再实现；不修改或删除公开测试及 expected 来制造通过；不针对 fixtures 或探针字符串过拟合；不改 `创始人专用/` 下文件，除非创始人明确要求。
- 结论必须基于实际执行：给出命令、退出码、日志、diff、SHA。未运行标 NOT RUN；建议与事实分开；不得用"测试通过"替代独立验收，学员不能自审批准自己的关键成果。
- 允许本地 `git init/commit/branch/worktree` 练习（仅在用户要求时提交）；禁止 force push、禁止推送到正式仓库。
- 引入新依赖、修改公共接口（例如迁移 `ordercheck.evidence` 兼容入口）、扩大输入格式，都需要先暂停并说明影响，由人决定。
