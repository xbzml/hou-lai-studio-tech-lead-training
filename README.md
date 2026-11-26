# OrderCheck Lab（纯合成训练项目）
这是独立的 Python 标准库练习项目，不是 OrderGuard 生产代码，也不是现有仓库的真实缺陷报告。Python 3.10+；无需联网或 API Key。初始代码仅为故意不完整的起点，公开冒烟测试通过不等于验收通过。

在本目录执行：
```bash
python -m unittest discover -s tests -v
python -m ordercheck fixtures/order_ok.txt
python -m ordercheck fixtures/order_missing.txt
```
可建立本地 Git 基线（先确认当前位置和文件，无需远程）：`git init`，检查 `git status`，提交初始版本。所有工作在练习仓库开展。正式 GitHub 仓库仅供 T00 只读对照；不得推送本练习内容至正式仓库。

先读 `SPEC.md`，按关卡逐步实现；不要一次要求 AI 完成全部功能。T02 保持简单，T03 增强证据和异常，T04 才考虑公共包。导师探针由创始人保存，训练时先独立设计测试。
