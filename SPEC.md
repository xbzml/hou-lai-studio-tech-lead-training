# 合成训练项目验收契约 v1

## 业务边界
模拟水泵订单完整性及合法值核验，不进行生产放行，不判断真实工程选型是否安全，不使用真实客户文件。输入为 UTF-8 TXT 单订单，`Key: Value` 每行一项，允许空白行，不允许重复键（忽略前后空白但键名区分大小写）、无法解析的非空行或未知键。只支持列出的键；不支持格式应明确失败，不猜测内容。

| 键 | 值要求 |
|---|---|
| Order ID | 非空，非 TBD/待定（大小写忽略） |
| Revision | 非空，非 TBD/待定 |
| Product | 必须为 Pump |
| Flow | 有限、正数，单位 `m3/h`（严格匹配，不做自动换算） |
| Head | 有限、正数，单位 `m` |
| Material | 非空，非 TBD/待定 |
| Quantity | 十进制正整数，不含单位 |

### T02 最小要求
`check_order(text: str) -> dict`，返回 `decision`（PASS 或 REVIEW）、`findings`（列表，每项有 `field` 与 `code`）。先做必填字段完整性和空值检查；PASS 只表示训练中的完整性检查。任何字段缺失或占位符应 REVIEW，`code` 为 MISSING_FIELD。正常例通过。不可把 PASS 对外解释为生产批准。

### T03 完整安全要求
严格解析，任何重复/未知键、不可解析行、非法值、单位不符、非有限/非正数均 REVIEW 或 BLOCK；正常样本 PASS。读取失败、非 UTF-8 输入、非 TXT 输入及执行异常返回 BLOCK（CLI 非零），禁止默认 PASS。非法/冲突的 findings 有明确 field/code。`check_order` 接口保留。CLI：`python -m ordercheck FILE` 输出 JSON；PASS 退出码 0，REVIEW 退出码 1，BLOCK 退出码 2。命令行路径应先确认后只读，不处理外部网络或真实文件。

### T03 证据接口（训练专用，不等于真实 Evidence Core）
保留 `make_pointer(document_id: str, raw: bytes, start: int, end: int) -> dict` 与 `verify_pointer(document_id: str, raw: bytes, pointer: dict) -> str`。pointer 含 `document_id`, `source_digest`（SHA-256 raw bytes hex）, `start`, `end`, `quote`（UTF-8 解码的 raw[start:end]）。字节位置半开区间，整数非 bool，`0 <= start < end <= len(raw)`；quote 必须非空，不能只依赖 `quote in raw`。`make_pointer` 对非法区间或解码错误抛 ValueError 或 UnicodeError；`verify_pointer` 在文档 ID、digest、区间、精确引用均相符且输入合法时 VERIFIED；不匹配 REJECTED，非法或无法解码输入 UNVERIFIABLE 或 REJECTED；绝不因异常返回 VERIFIED。raw 必须由可信测试调用者提供，外部 pointer 不授予信任；本练习不模拟真实存储身份、同内容替换或授权系统，生产 Core 另有更严格契约。

版本变化练习：对先前 PASS 结果绑定原始 SHA-256，变更 raw（哪怕合法字段）时原结论不得继续使用，重新核验。自拟接口并在报告解释。训练中不实现自动审批。

### T04 跨场景
公共包只做证据核验，不含 Order ID、Quantity 或合同交付物规则。合同样本 `contract.txt`、`handover.txt`（本训练仅 TXT；正式项目 #25 使用 TXT/EML，以实际 Issue 为准）。按项目 ID 和版本一致性及 required/delivered 的逗号分隔集合核对，缺失 Deployment Package 返回 REVIEW/MISSING_DELIVERABLE。必须覆盖正常、缺失、错误证据、版本不一致、来源变更、不支持输入。固定版本/哈希；非原作者独立安装；第二场景期间 Core 变更 0；有缺口暂停，不能复制源码掩盖。保留原 `ordercheck.evidence` 兼容入口或书面获批迁移并让导师调整探针；不得直接修改隐藏测试以求通过。
