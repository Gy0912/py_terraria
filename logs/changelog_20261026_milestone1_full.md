# Changelog — 2026-10-26 Milestone 1 完整实现

## 修改

### `world.py` — 地形生成增强
- **目的**：让世界不再只有单调的地表层，增加探索价值。
- **变化**：5 阶段生成 — ① 平滑高度曲线 ② 地表/地下30层（grass→dirt→stone / sand）③ 矿石散布（iron_ore/copper_ore/gold_ore 概率）④ 随机洞穴（球形移除）⑤ 树木（forest/jungle/snow 地表生长 wood+leaves）。
- **影响**：瓦片总数约 130K（0.04s 初始化）；新增 `_surface_heights` 供生物生成使用。

### `settings.py` — 新增瓦片颜色
- **变化**：`TILE_COLORS` 增加 `leaves`、`iron_ore`、`copper_ore`、`gold_ore`。
- **影响**：所有新瓦片类型均可在屏幕上以颜色区分。

### `game.py` — 整合战斗/物品栏/HP/MP/生物
- **变化**：
  - 导入并实例化 `HealthBar`、`ManaBar`、`CreatureManager`、`InventoryUI`。
  - `update()` 增加落下伤害应用、生物更新、碰撞伤害（含无敌帧）。
  - `events()` 左键先检测攻击生物，再挖掘瓦片；右键通过 InventoryUI 获取选中方块。
  - `draw()` 渲染生物、HP/MP 条、底部工具栏。
  - HUD 简化为坐标/群系/FPS。

### `player.py` — 落下伤害
- **变化**：追踪 `fall_start_y`，着陆时计算落距，>8 格触发 `fall_damage`。
- **影响**：高处跳下有实际 HP 损失。

## 新增

### `creatures.py`
- `Creature`：28×32 红色方块敌人，横向巡逻、重力、瓦片碰撞、HP 30、接触伤害 8。
- `CreatureManager`：自动在玩家附近地表生成敌人（最多 8 个，300 帧冷却），远距离消失。
- **目的**：Milestone 1 要求的最小战斗循环。

### `inventory.py`
- `InventoryUI`：底部 9 格快捷栏，预设 dirt/stone/sand/wood/leaves，数字键/滚轮选择，显示物品颜色与数量。
- **目的**：替代 HUD 文本式物品栏，提供直观的方块选择与计数。

### `healthbar.py`
- `HealthBar`：右上角红色 HP 条 + 数值文本。
- **目的**：可视化生命值，配合落下伤害与生物碰撞。

### `manabar.py`
- `ManaBar`：HP 下方蓝色 MP 条（当前为预留，无消耗机制）。
- **目的**：为后续法术/技能预留 UI。

## 验证

- 全部模块 headless 冒烟通过（World 0.04s / 130K tiles, Creature spawn OK, InventoryUI OK）。
- **桌面窗口运行未测试**。
