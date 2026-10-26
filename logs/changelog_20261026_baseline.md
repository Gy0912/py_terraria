# Changelog — 2026-10-26 工程基线

## 新增

- `.gitignore`：排除 Python 缓存、虚拟环境、IDE 与构建产物；**不**忽略 `images/`。
- `AGENTS.md`：Agent 协作边界、主项目/只读参考路径、小步增量与测试诚实性要求。
- `README.md`：项目树、当前状态摘要、未验证的运行说明。
- `docs/PROJECT_STATUS.md`：模块清单、实现/缺口、风险与冒烟步骤。
- `docs/ROADMAP.md`：Milestone 0～6 提案（含目的、交付物、验收、风险、非目标）。
- `docs/GAME_DESIGN.md`：设计简报、创新假设、Demo 评估方式、竞品调研问题与对比框架（pending）。

## 修改

- 无游戏源码（`.py`）与 `images/` 资源变更。

## 工程操作

- 创建外部备份：`D:\lab_files\game\py_terraria_backup_20261026`（已核对 10 个 `.py`、13 张 JPG）。
- 在主项目目录执行 `git init`（未 `add`/`commit`）。

## 目的与影响

- **目的**：在不动玩法代码的前提下建立可恢复备份、本地版本跟踪与文档基线，供长期单人迭代与 Agent 交接。
- **影响**：后续任务可依赖统一文档判断范围；Git 跟踪需用户审阅后首次提交；`__pycache__` 将不再进入版本库。
