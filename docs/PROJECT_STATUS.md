# 项目状态（PROJECT_STATUS）

**更新日期**：2026-10-26  
**当前里程碑**：Milestone 1 — 最小可玩基础（进行中）

本文区分：**已验证** | **静态推断** | **未测试**

---

## 文件与模块

| 路径 | 说明 | 状态 |
|------|------|------|
| `game.py` | 入口、`Game` 类：开始界面、主循环、瓦片渲染、挖掘/放置、HUD | 已修改 |
| `settings.py` | 窗口、地图常量、`TILE_COLORS`、`IMAGES_PATH` | 已修改（加入瓦片颜色） |
| `world.py` | `World`：按需群系查询、稀疏瓦片 dict、地形生成 | **重写**（去除稠密矩阵） |
| `background.py` | 群系背景加载与视差绘制 | 未修改 |
| `player.py` | `Player`：重力、碰撞检测、跳跃、物品栏、绘制 | **重写** |
| `camera.py` | `Camera`：跟随玩家、世界→屏幕坐标转换 | **重写** |
| `creatures.py` | 占位（空文件） | 未修改 |
| `inventory.py` | 占位（空文件） | 未修改 |
| `healthbar.py` | 占位（空文件） | 未修改 |
| `manabar.py` | 占位（空文件） | 未修改 |
| `images/` | 13 张 JPG + 开始图 | 未修改 |

---

## 已实现功能

| 功能 | 状态 | 依据 |
|------|------|------|
| Pygame 窗口与 60 FPS 循环 | **已验证**（headless） | `game.py` |
| 开始界面 + Enter 开始 | **静态推断** | `game.py show_start_screen()` |
| 群系按需查询（无稠密矩阵） | **已验证**（headless） | `world.py get_biome()` |
| 稀疏瓦片地形（地表 grass/dirt/stone/sand） | **已验证**（38000 tiles, 0.01s） | `world.py generate_terrain()` |
| 玩家渲染 + 相机跟随 | **已验证**（headless init） | `player.py draw()` + `camera.py` |
| 玩家重力 + 碰撞检测 | **静态推断** | `player.py update()` |
| 左键挖掘方块 → 物品栏 | **静态推断** | `game.py events()` |
| 右键放置方块 | **静态推断** | `game.py events()` |
| 数字键 1-4 选择方块类型 | **静态推断** | `game.py events()` |
| HUD：坐标、群系、FPS、物品栏、选中方块 | **静态推断** | `game.py _draw_hud()` |
| 鼠标悬停瓦片高亮 | **静态推断** | `game.py _draw_cursor_highlight()` |
| 背景随群系与玩家坐标视差 | **已验证**（headless init） | `background.py` |

---

## 未实现 / 待做

- 战斗系统、生物 AI
- 血条 / 蓝条 HUD
- 完整物品栏 UI
- 存档 / 读档
- 精灵与动画（当前全为色块）
- 暂停 / 游戏结束界面
- 更丰富的地形生成（矿石、树木、洞穴）
- 音效与背景音乐

---

## 架构改进记录

1. **World 存储**：由 5000×1000 稠密矩阵改为稀疏 `dict`（键 `(tx,ty)` → 方块类型）+ 按需群系查询。初始化从未知（可能数秒 + 数百 MB）降至 **0.01 秒 / 38000 条目**。
2. **Camera**：从独立输入改为跟随 Player，提供 `apply()` 坐标转换。
3. **Player**：增加重力、碰撞、物品栏属性；`draw()` 已在 `game.py` 主循环中调用。

---

## 运行时与测试

| 项 | 状态 |
|----|------|
| 入口命令 `python game.py`（项目根） | **headless 冒烟已通过**（所有模块初始化成功） |
| 完整游戏窗口运行 | **未测试**（需要桌面环境 + 用户手动验证） |
| 依赖 | pygame 2.6.1（MSYS2 Python 3.14.8，通过 pacman 安装） |

### 手动冒烟步骤

1. `Set-Location D:\lab_files\game\py_terraria`
2. `python game.py`
3. 预期：开始界面 → Enter → 进入游戏
4. 验证：玩家绿色矩形可见、WASD 移动/跳跃、背景随群系变化、地面瓦片可见
5. 验证：左键挖掘、右键放置、数字键切换、HUD 显示

---

## 重要未知项

- 桌面环境下完整渲染帧率是否稳定
- 大量瓦片在视口边界渲染的性能
- pygame 2.6.1 + Python 3.14 在窗口模式下是否存在兼容问题
