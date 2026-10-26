# 项目状态（PROJECT_STATUS）

**更新日期**：2026-10-26  
**版本**：0.2.0  
**当前里程碑**：Milestone 1 已完成；按用户要求提前实现了 Milestone 2–4 的部分内容（群系环境关联、战斗、制作）

本文区分：**已验证（冒烟测试）** | **已验证（截图人工检查）** | **未验证**

---

## 模块与依赖关系

```
game.py ─┬─ world.py ── worldgen.py ── tiles.py
         ├─ player.py ── physics.py, inventory.py, items.py
         ├─ actions.py ── (world, player, creatures, entities)
         ├─ creatures.py ── physics.py
         ├─ entities.py ── physics.py, items.py
         ├─ render.py / lighting.py / minimap.py ── world.py, textures.py
         ├─ textures.py ── tiles.py, items.py
         └─ inventory.py / healthbar.py / manabar.py / ui.py
```

- 世界数据：`World.chunks[(cx, cy)]` 为 16×16 的 `bytearray`（方块 id），首次访问时由 `WorldGen.generate_chunk` 生成。每个方块都是 `(种子, x, y)` 的纯函数，相邻区块可以按任意顺序生成，结果一致。
- 修改方块会递增 `chunk_version`，渲染缓存与小地图据此失效并重建。

---

## 功能状态

| 功能 | 状态 | 依据 |
|------|------|------|
| 区块懒加载，从地表到地狱全深度无空洞 | 已验证（冒烟 + 全图渲染检查） | `world.py`、`worldgen.py` |
| 群系 / 层级相对本地地表高度判定 | 已验证 | `World.layer_at`、`get_biome` |
| 五个群系各有专属方块（雪 / 冰、泥浆 / 丛林草、沙 / 砂岩等） | 已验证（全图渲染检查） | `WorldGen.base_tile` |
| 300 个种子都能生成完整的沙漠 / 雪原 / 丛林 | 已验证 | `WorldGen._biome_strips` |
| 程序化像素贴图（方块、物品、玩家、16 种怪物） | 已验证（截图） | `textures.py` |
| 挖掘为多次敲击的过程 + 裂纹 4 阶段 + 碎屑粒子 | 已验证（冒烟：草地 31 帧） | `actions.hit_tile`、`render.draw_cracks` |
| 掉落物弹出、吸附、拾取 | 已验证 | `entities.ItemDrop` |
| 砍树整棵倒下并掉落木材 | 已验证 | `World.remove_tree` |
| 放置方块与制作站（支撑规则） | 已验证 | `actions.place_tile` |
| 制作界面（22 个配方、附近制作站检测） | 已验证 | `inventory.py`、`items.RECIPES` |
| 站立 / 往下挖不再掉血（第 5 条 bug） | 已验证（站立 300 帧、下挖 25 格均不掉血） | `Player.update` 的 `fall_peak` |
| 真实的高处坠落仍有伤害 | 已验证（40 格坠落 −84） | `FALL_SAFE_TILES = 12` |
| 怪物按层级 / 群系 / 昼夜刷新 | 已验证（沙漠、雪原、丛林场景） | `creatures.spawn_table` |
| 近战击杀与材料掉落 | 已验证（铜短剑击杀史莱姆得凝胶） | `actions.update_use` |
| 弓箭、法杖、消耗品 | 未单独验证（代码路径与近战共用） | `actions.try_use` |
| 死亡界面、复活 | 已验证 | `Game._death_event` |
| 开始界面鼠标按钮、暂停菜单 | 已验证（截图）；点击路径未自动化 | `Game.show_start_screen` |
| 昼夜与光照 | 已验证（截图） | `lighting.py` |
| 小地图 | 已验证（截图） | `minimap.py` |
| 性能 | 已验证：无窗口模式下 update+draw 约 10.4 ms/帧 | `tools/smoke_test.py` |

---

## 本次修复的 bug 根因

1. **往下挖会自动掉血**：旧代码的 `fall_start_y` 只在跳跃时重置，而站立时重力让玩家每帧都"落地"一次，往下挖 8 格以上后每帧都会触发跌落伤害。现在改为记录"上次站稳以来的最高点" `fall_peak`，只在真正从空中落地的那一帧结算。
2. **地下有未生成区域、地上被判成地下**：旧世界只预生成了地表附近 30 格厚的一层（实际没有任何懒加载代码）；群系分层使用固定行号，而地表在其上下起伏。现在改为区块懒加载 + 相对本地地表的分层判定。
3. **碰撞边缘取整**：玩家底边的小数部分被向下取整，导致站立时 `on_ground` 隔帧翻转（跳跃可能失灵）。`physics._span` 改为对右边 / 下边向上取整。
4. **原世界生成的沙漠可能缺失**：放置循环遇到同侧位置会直接放弃。现在保证两段沙漠分居中心森林两侧。
5. **Windows 字体枚举崩溃**：`pygame.font.SysFont` 在本机读取注册表时抛 `TypeError`。现在直接加载 `C:\Windows\Fonts\msyh.ttc` 等文件。

---

## 未实现 / 待做

- 存档 / 读档（每次进入都是新世界）
- 音效与音乐
- Boss 战（晶状体已作为法杖材料，后续可用作召唤物）
- 盔甲 / 防御装备、NPC、液体流动
- 背景墙仅覆盖地表下 30 格；更深处显示群系背景图

---

## 运行时与测试

| 项 | 状态 |
|----|------|
| `python tools/smoke_test.py` | **29/29 通过**（MSYS2 Python 3.14.8 + pygame 2.6.1，无窗口模式） |
| `python game.py` 桌面窗口 | **未验证**：本机任务没有打开真实窗口，需要用户手动试玩 |
| 依赖 | `requirements.txt`：`pygame>=2.5` |

### 手动试玩检查清单

1. 开始界面：鼠标点击"开始游戏"、"退出游戏"都有效，按钮有悬停高亮。
2. 按住左键挖泥土：大约 0.5 秒，能看到裂纹逐级加深；方块碎后弹出掉落物并飞向玩家。
3. 往下挖 30 格以上：生命值不应下降；周围逐渐变暗，只有玩家周围有光；放置火把可以照亮。
4. 用斧头砍树：整棵树倒下，得到若干木材；按 E 用 10 个木材制作工作台。
5. 走到雪原 / 丛林 / 沙漠：地面方块和出现的怪物都应随之变化；夜晚森林会出现僵尸和恶魔眼。
6. 生命归零：出现"你死了"界面；"复活"回到出生点，"返回主菜单"回到开始界面。
7. 右上角：生命条、魔力条，下面是小地图（M 键缩放）。

---

## 已知风险

- 光照在纯 Python 中逐格计算，火把很密集时可能掉帧（目前单帧约 10 ms）。
- 已探索区块常驻内存，长时间远距离探索后内存会持续增长（未测量）。
- `start_screen.jpg` 含 Terraria 官方标志，公开发布前需要替换。
