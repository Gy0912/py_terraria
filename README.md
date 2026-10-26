# PyTerraria

早期阶段的 2D 沙盒生存冒险游戏（Python + Pygame）。项目处于积极开发中，当前以工程基线与小型可玩增量为目标，而非完整商业级内容。

## 当前状态（摘要）

- **已有**：开始界面、主循环、群系按需查询、视差背景、地形（地表/地下30层/矿石/洞穴/树木）、玩家重力碰撞与跳跃、相机跟随、挖掘/放置/攻击、生物系统（巡逻/碰撞伤害/击杀）、HP/MP 条、9 格工具栏 UI、HUD。
- **缺失**：精灵动画、合成系统、存档、暂停/结束界面、音效、MP 消耗等。
- 详情见 [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md)。

## 项目结构

```
py_terraria/
├─ game.py              # 游戏入口、主循环、瓦片渲染、事件（挖掘/放置/攻击）、HUD
├─ settings.py          # 窗口、地图尺寸、颜色、瓦片颜色（含矿石/树）、图片路径
├─ world.py             # 按需群系查询 + 稀疏瓦片 dict + 地形生成（含矿石/洞穴/树木）
├─ background.py        # 背景图加载与视差绘制（Background）
├─ player.py            # 玩家移动/重力/碰撞/跳跃/落下伤害/物品栏/绘制
├─ camera.py            # 相机跟随玩家 + 世界→屏幕坐标转换
├─ creatures.py         # 基础敌人 AI、碰撞伤害、CreatureManager
├─ inventory.py         # 底部 9 格工具栏 UI（数字键/滚轮切换）
├─ healthbar.py         # 右上角 HP 条
├─ manabar.py           # HP 下方 MP 条（预留）
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

**预期行为**：

1. 显示开始界面（`start_screen.jpg`），按 Enter 进入游戏。
2. 玩家（绿色矩形）站在地表，WASD/方向键 移动，W/Space 跳跃。
3. 相机自动跟随玩家；背景随群系变化。
4. 左键挖掘方块（加入物品栏），右键放置选中方块，数字键 1-4 切换方块类型。
5. 顶部 HUD 显示坐标、群系、FPS、物品栏与选中方块。
6. ESC 退出游戏。

**已通过 headless 冒烟测试（所有模块初始化 + World 0.01s）；桌面窗口运行需用户手动验证。**

## 文档

| 文件 | 用途 |
|------|------|
| [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) | 实现状态、风险、未知项 |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | 里程碑提案（非承诺排期） |
| [`docs/GAME_DESIGN.md`](docs/GAME_DESIGN.md) | 设计原则、Demo 评估、竞品调研问题 |

## 许可与参考

本仓库为原创开发项目。`PyRarria-master` 仅作只读参考，不得将其代码或资源默认可复制进本仓库。
