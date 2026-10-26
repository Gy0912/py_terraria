# Agent 协作说明（PyTerraria）

## 愿景

长期、单人开发的 2D 沙盒生存冒险游戏（Python + Pygame）。借鉴 Terraria 等游戏的**玩法方向**，但不克隆任何单一作品；通过小型可玩 Demo 探索机制，再逐步组合成原创体验。

## 路径边界

| 范围 | 路径 |
|------|------|
| **可写主项目** | `D:\lab_files\game\py_terraria` |
| **只读参考** | `D:\lab_files\game\PyRarria-master`（禁止修改、移动、删除；未经用户明确批准不得复制其代码或资源） |
| **禁止** | 在 `D:\lab_files\game` 根目录或参考项目中执行 `git init` |

## 技术栈（已确认）

- Python 3.10+（本机已验证：MSYS2 UCRT64 Python 3.14.8；该环境禁止 pip，pygame 需用 pacman 安装）
- Pygame（唯一第三方依赖，见 `requirements.txt`；本机已验证 2.6.1）

## 工作方式

1. **小步增量**：每次任务聚焦少量文件与可验证结果，避免大范围重写。
2. **先读再改**：动手前检查 `docs/PROJECT_STATUS.md` 与相关源码，不臆测架构。
3. **文档同步**：架构、里程碑或验收方式变化时，更新 `README.md`、`docs/PROJECT_STATUS.md`，并在 `logs/` 中记录 changelog（说明目的与影响）。
4. **依赖与资源**：不擅自添加依赖、下载资源或大规模重构；新依赖需用户同意并写入依赖清单。
5. **诚实测试**：未实际运行相关命令或游戏时，不得声称功能已测试通过。
6. **创意边界**：不擅自重新定义游戏创意方向；设计探索见 `docs/GAME_DESIGN.md` 与 `docs/ROADMAP.md`（里程碑 1 及以后为**提案**，非自动执行任务）。

## 自动验证

改动玩法或渲染后运行 `python tools/smoke_test.py`（项目根目录，无窗口）。它会用模拟输入驱动真实的游戏循环，并把截图写入 `tools/screenshots/`。新增机制时，请同步补充对应的检查项。

## 手动验证要求

完成可运行相关改动后，在交付说明中写明：

- 工作目录（须为项目根，以便 `images/` 相对路径有效）
- 执行的命令
- 预期可见行为与实际结果（若未运行则标注「未验证」）

## 关键文档

- `README.md` — 结构与运行说明
- `docs/PROJECT_STATUS.md` — 实现状态与风险
- `docs/ROADMAP.md` — 里程碑提案
- `docs/GAME_DESIGN.md` — 设计简报与竞品调研问题
