# 项目状态（PROJECT_STATUS）

**更新日期**：2026-10-26  
**当前里程碑**：Milestone 1 — 最小可玩基础（核心完成，待桌面验证）

本文区分：**已验证** | **静态推断** | **未测试**

---

## 文件与模块

| 路径 | 说明 | 状态 |
|------|------|------|
| `game.py` | 入口、主循环、瓦片渲染、事件（挖掘/放置/攻击）、HUD | 已实现 |
| `settings.py` | 窗口、地图常量、`TILE_COLORS`（含矿石/树木）、`IMAGES_PATH` | 已实现 |
| `world.py` | 按需群系查询 + 稀疏瓦片 dict + 地形生成（地表/地下/矿石/洞穴/树木） | 已实现 |
| `background.py` | 群系背景加载与视差绘制 | 未修改 |
| `player.py` | 重力/碰撞/跳跃/物品栏/落下伤害/绘制 | 已实现 |
| `camera.py` | 跟随玩家 + 世界→屏幕坐标转换 | 已实现 |
| `creatures.py` | `Creature` + `CreatureManager`：基础敌人AI、碰撞伤害、点击攻击 | 已实现 |
| `inventory.py` | `InventoryUI`：底部 9 格工具栏、数字键/滚轮选择 | 已实现 |
| `healthbar.py` | `HealthBar`：右上角 HP 条 | 已实现 |
| `manabar.py` | `ManaBar`：HP 下方 MP 条（预留） | 已实现 |
| `images/` | 13 张群系 JPG + 开始图 | 未修改 |

---

## 已实现功能

| 功能 | 状态 | 依据 |
|------|------|------|
| 开始界面 + Enter 开始 | 静态推断 | `game.py` |
| 60 FPS 主循环 | **已验证**（headless） | `game.py` |
| 群系按需查询 | **已验证** | `world.py` |
| 地形生成：地表/dirt/stone + 矿石(iron/copper/gold) + 洞穴 + 树木 | **已验证**（~130K tiles, 0.04s） | `world.py` |
| 玩家渲染 + 相机跟随 | **已验证**（headless init） | `player.py` + `camera.py` |
| 玩家重力 + 瓦片碰撞 | 静态推断 | `player.py` |
| 跳跃（W/Space/Up） | 静态推断 | `player.py` |
| 落下伤害（>8 格） | 静态推断 | `player.py` + `game.py` |
| 左键挖掘方块 → 物品栏 | 静态推断 | `game.py` |
| 左键攻击生物（15伤害） | 静态推断 | `game.py` |
| 右键放置选中方块 | 静态推断 | `game.py` |
| 底部 9 格工具栏 UI（数字键/滚轮） | **已验证**（headless） | `inventory.py` |
| 生物系统：巡逻/碰撞伤害/生成/消亡 | **已验证**（headless spawn） | `creatures.py` |
| HP 条 + MP 条 | **已验证**（headless init） | `healthbar.py` + `manabar.py` |
| HUD：坐标/群系/FPS | 静态推断 | `game.py` |
| 鼠标瓦片高亮 | 静态推断 | `game.py` |
| 背景视差（12种群系） | **已验证**（headless init） | `background.py` |

---

## 未实现 / 待做

- 精灵与动画（当前全为色块）
- 完整合成系统
- 存档 / 读档
- 暂停 / 游戏结束界面逻辑
- 音效与背景音乐
- 更复杂的生物类型（飞行、Boss）
- MP 实际消耗机制（当前仅 UI）
- 更深层地形（按需加载）

---

## 运行时与测试

| 项 | 状态 |
|----|------|
| 入口命令 `python game.py`（项目根） | **headless 冒烟已通过** |
| 桌面窗口运行 | **未测试** |
| 依赖 | pygame 2.6.1（MSYS2 Python 3.14.8） |

### 手动冒烟步骤

1. `Set-Location D:\lab_files\game\py_terraria`
2. `python game.py`
3. 预期：开始界面 → Enter → 游戏
4. 验证：WASD 移动 + 跳跃、地面/树木/矿石可见、左键挖掘/攻击、右键放置
5. 验证：HP/MP 条、底部工具栏、鼠标高亮、生物出现并可击杀

---

## 重要未知项

- 桌面渲染帧率是否稳定
- 生物碰撞判定手感
- 大范围挖掘后内存趋势
