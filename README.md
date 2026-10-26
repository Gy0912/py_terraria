# PyTerraria

早期阶段的 2D 沙盒生存冒险游戏（Python + Pygame）。项目处于积极开发中，当前以工程基线与小型可玩增量为目标，而非完整商业级内容。

## 当前状态（摘要）

- **已有**：开始界面、主循环、群系分层世界数据、视差背景切换、玩家移动逻辑（部分未接入渲染）。
- **缺失或未接线**：方块地形、挖掘/建造、战斗、物品、HUD、相机与玩家的整合等。
- 详情见 [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md)。

## 项目结构

```
py_terraria/
├─ game.py              # 游戏入口与主循环（Game 类）
├─ settings.py          # 窗口、地图尺寸、颜色、图片路径常量
├─ world.py             # 群系地图生成与查询（World）
├─ background.py        # 背景图加载与视差绘制（Background）
├─ player.py            # 玩家移动与绘制（Player；主循环未调用 draw）
├─ camera.py            # 相机位移草稿（未接入 game.py）
├─ creatures.py         # 占位（空文件）
├─ inventory.py         # 占位（空文件）
├─ healthbar.py         # 占位（空文件）
├─ manabar.py           # 占位（空文件）
├─ images/              # 位图资源（JPG）
│  ├─ screen_pics/      # 开始界面等
│  └─ background_pics/  # 各群系/层背景
├─ docs/                # 状态、路线图、设计文档
├─ logs/                # 变更记录（changelog）
├─ AGENTS.md            # Agent 协作与边界
└─ .gitignore           # Git 忽略规则（不含 images/）
```

只读参考项目（勿在本仓库内修改）：`D:\lab_files\game\PyRarria-master`。

## 依赖

- **已确认**：运行时代码依赖 **Pygame**（见各 `.py` 中的 `import pygame`）。
- **未确认**：具体 Pygame / Python 版本要求；仓库内尚无 `requirements.txt`（可在后续里程碑补充）。

## 运行方式（未在本机任务中验证）

在 PowerShell 中从**项目根目录**执行（保证 `images/` 相对路径正确）：

```powershell
Set-Location "D:\lab_files\game\py_terraria"
python -m pip install pygame
python game.py
```

**预期行为（据源码静态阅读，未运行验证）**：

1. 显示开始界面（`start_screen.jpg`），按 Enter 进入游戏。
2. 主循环中背景随玩家移动与当前群系变化；玩家矩形绘制逻辑存在但 `game.py` 的 `draw()` 未调用 `player.draw()`，因此**可能看不到玩家实体**。
3. 首次进入新局时 `World` 会构建大型群系网格，启动耗时与内存占用可能较高（见 `docs/PROJECT_STATUS.md`）。

## 文档

| 文件 | 用途 |
|------|------|
| [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) | 实现状态、风险、未知项 |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | 里程碑提案（非承诺排期） |
| [`docs/GAME_DESIGN.md`](docs/GAME_DESIGN.md) | 设计原则、Demo 评估、竞品调研问题 |

## 许可与参考

本仓库为原创开发项目。`PyRarria-master` 仅作只读参考，不得将其代码或资源默认可复制进本仓库。
