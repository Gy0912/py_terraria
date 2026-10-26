# 项目状态（PROJECT_STATUS）

**更新日期**：2026-10-26  
**当前里程碑**：Milestone 0 — 工程基线（进行中：文档与本地 Git 已建立；冒烟测试流程已定义但未执行）

本文区分：**已验证事实** | **静态推断** | **未测试**

---

## 文件与模块

| 路径 | 说明 | 依据 |
|------|------|------|
| `game.py` | 入口、`Game` 类、开始界面、主循环 | 源码 |
| `settings.py` | `TITLE`、分辨率、地图/层高度、`IMAGES_PATH` | 源码 |
| `world.py` | `World.generate_biomes()`、`get_biome()` | 源码 |
| `background.py` | 群系背景加载、视差 `draw` | 源码 |
| `player.py` | 移动、`draw` 矩形 | 源码 |
| `camera.py` | 键盘移动相机坐标 | 源码；**未接入** `game.py` |
| `creatures.py` | 空 | 源码 |
| `inventory.py` | 空 | 源码 |
| `healthbar.py` | 空 | 源码 |
| `manabar.py` | 空 | 源码 |
| `images/` | 13 张 JPG + 开始图 | 文件系统 |

**已验证事实**：主项目根目录约 10 个 `.py` 与 `images/`；存在 `__pycache__/`（应由 `.gitignore` 排除）。

---

## 已实现功能（静态推断，未运行游戏）

| 功能 | 状态 | 备注 |
|------|------|------|
| Pygame 窗口与 60 FPS 循环 | 推断已实现 | `game.py` `run()` |
| 开始界面 + Enter 开始 | 推断已实现 | `show_start_screen()` |
| 群系条带 + 垂直分层（space/地表/地下/cave/hell） | 推断已实现 | `world.py` |
| 背景随群系与玩家坐标视差 | 推断已实现 | `background.py` + `game.update/draw` |
| 玩家 WASD 移动与地图边界 | 推断已实现 | `player.py`；坐标用于背景 |
| 玩家精灵/矩形渲染 | **未接线** | `player.draw` 未被 `game.draw` 调用 |
| 相机跟随 | **未实现** | `camera.py` 未使用 |
| 方块、交互、战斗、物品、HUD | **未实现** | 无逻辑或空文件 |
| 暂停 / 游戏结束界面 | **占位** | `pause_screen`、`show_game_over_screen` 为 `pass` |

---

## 架构与性能风险（静态推断）

1. **稠密群系网格**：`ACTUAL_MAP_WIDTH` × `ACTUAL_MAP_HEIGHT`（`settings.py`：约 5000×1000 格）在 `World.__init__` 中一次性分配二维列表 — **启动成本与内存未测试**。
2. **玩家与世界坐标系**：玩家使用像素坐标；`get_biome` 除以 `TILE_SIZE` — 需后续统一「世界 / 屏幕 / 相机」模型（**设计待定**）。
3. **死代码与空模块**：`game.py` 导入 `creatures`、`camera` 但未使用，易造成误判进度。
4. **无依赖锁定、无自动化测试**：环境差异与回归只能靠手动冒烟。

---

## 运行时与测试

| 项 | 状态 |
|----|------|
| 入口命令 `python game.py`（项目根） | **未测试**（本轮任务禁止启动游戏） |
| 依赖安装 | **未测试**；推断需要 `pygame` |
| 单元 / 集成测试 | **不存在** |

### 建议的手动冒烟步骤（Milestone 0 交付物，待执行）

1. `Set-Location D:\lab_files\game\py_terraria`
2. 确认已安装 Pygame 后运行 `python game.py`
3. 记录：启动耗时、是否异常退出、开始界面是否显示、Enter 后背景是否随按键变化
4. 可选：观察任务管理器中进程内存峰值（尤其首次 `World()` 创建时）

---

## 工程基线（Milestone 0）

| 项 | 状态 |
|----|------|
| 外部备份 | **已验证** `D:\lab_files\game\py_terraria_backup_20261026`（10 个 `.py`，13 张 JPG） |
| 主项目 `.git` | 见本轮 `git init` 结果 |
| 文档 | `README.md`、`AGENTS.md`、`docs/*` |
| Git 提交 | **未执行**（等待用户审阅文件列表） |

---

## 重要未知项

- Pygame / Python 推荐版本组合
- `World` 全量矩阵是否可接受，或应改为分块/按需生成
- 与只读参考项目 `PyRarria-master` 的长期关系（仅借鉴概念 vs 逐步移植模块）— **需用户决策**
- 目标发布平台（桌面仅 / 未来 Android 等）— **未定义**
