# Changelog — 2026-10-26 Milestone 1 基础实现

## 修改

### `world.py` — 完全重写
- **目的**：消除 5000×1000 稠密 biome_map 矩阵导致的启动性能问题（原为 500 万条目）。
- **变化**：改为 100 元素 biome_strips + 按需 `get_biome()` 计算；瓦片存储为稀疏 dict `tiles`（约 38000 条目）。
- **影响**：World 初始化降至 0.01 秒；`get_biome` 返回值与原逻辑完全一致。新增 `generate_terrain()` 在地表生成 grass/dirt/stone/sand 方块。新增 `get_tile`/`set_tile`/`remove_tile` API。

### `player.py` — 完全重写
- **目的**：让玩家实际可见、可操作，支持重力与碰撞。
- **变化**：增加 `gravity`、`jump_power`、`on_ground`、`vx/vy` 物理；`_collides_with_world` 检测瓦片碰撞；`draw(surface, camera)` 使用相机偏移绘制；增加 `inventory` dict 和 `selected_block`。
- **影响**：Player 现为带物理的实体而非无碰撞坐标。

### `camera.py` — 完全重写
- **目的**：提供跟随玩家的视口。
- **变化**：`update(target_x, target_y)` 居中并钳制到世界边界；`apply(wx, wy)` 世界→屏幕坐标转换。
- **影响**：所有绘制通过 Camera.apply 定位。

### `game.py` — 大幅修改
- **目的**：接入新的 Camera/Player/World API，增加瓦片渲染、挖掘/放置与 HUD。
- **变化**：
  - `new()` 创建 Camera 实例；`update()` 调用 `camera.update`。
  - `draw()` 调用 `player.draw`、`_draw_tiles`、`_draw_hud`、`_draw_cursor_highlight`。
  - `events()` 处理鼠标左键挖掘、右键放置、数字键选择方块、ESC 退出。
  - 版本号更新至 0.1.0。
- **影响**：游戏从"仅背景切换"变为可看到地形、玩家、可交互的原型。

### `settings.py` — 增量修改
- **变化**：新增 `TILE_COLORS` dict，定义 grass/dirt/stone/sand/wood 的占位颜色。
- **影响**：为瓦片渲染提供颜色映射。

## 新增

- `logs/changelog_20261026_milestone1_foundation.md`：本文件。

## 未修改

- `background.py`、`creatures.py`、`inventory.py`、`healthbar.py`、`manabar.py`、`images/`

## 验证

- Headless 冒烟测试通过：World 0.01s 初始化、Player/Camera/Background 均正常创建。
- **未在桌面窗口中运行**（需用户手动验证渲染与交互）。
