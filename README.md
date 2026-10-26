# PyTerraria

早期阶段的 2D 沙盒生存冒险游戏（Python + Pygame），玩法参考 Terraria，但目标是逐步形成原创组合。项目处于积极开发中。

## 当前状态（v0.2.0）

- **世界**：5000×1000 格，按 16×16 区块懒加载；海洋 / 森林 / 雪原 / 丛林 / 沙漠五种地表群系，地表→地下→洞穴→地狱分层；洞穴、矿脉、树木、仙人掌、蘑菇、陶罐、生命水晶、海水与岩浆。
- **视觉**：程序化像素贴图（方块、物品、玩家、怪物），方块边缘描边与圆角，浅层地下背景墙，昼夜与火把光照，挖掘裂纹与粒子。
- **玩法**：按住左键持续挖掘（裂纹逐级显示）→ 掉落物弹出 → 靠近自动吸附拾取；斧头砍倒整棵树；放置方块 / 火把 / 制作站；40 格背包 + 制作界面（工作台 / 熔炉 / 铁砧，22 个配方）；近战挥砍、弓箭、法杖（消耗魔力）、治疗物品、生命水晶。
- **环境关联**：每个群系 / 层级的方块种类不同，怪物按「层级 + 群系 + 昼夜」刷新（16 种怪物，三类 AI：史莱姆跳跃、行走追击、飞行），各自掉落与环境相关的材料。
- **界面**：开始界面（鼠标点击开始 / 退出）、暂停菜单、死亡界面（复活 / 返回主菜单）、右上角生命 / 魔力条与小地图。
- 详情见 [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md)。

## 项目结构

```
py_terraria/
├─ game.py              # 入口；Game：开始/暂停/死亡界面、主循环、更新与绘制编排、HUD
├─ settings.py          # 屏幕、世界尺寸与分层行号、昼夜长度、字体与图片路径、中文名称
├─ tiles.py             # 方块注册表：固体/液体、耐久、所需镐力、掉落物、光源、制作站
├─ items.py             # 物品注册表（方块/工具/武器/消耗品/材料）、制作配方、初始物品
├─ worldgen.py          # 基于种子的确定性噪声地形：群系带、地表高度、洞穴、矿脉、树木与装饰
├─ world.py             # 区块存储与懒加载、方块读写、挖掘进度、光源索引、群系/层级查询
├─ player.py            # 玩家物理（台阶自动上跨、游泳、跌落伤害）、生命/魔力、受伤与复活、绘制
├─ actions.py           # 物品使用：挖掘过程、砍树、放置、挥砍判定、射击、消耗品、快速治疗
├─ creatures.py         # 怪物类型表、三类 AI、按环境的刷怪表与 CreatureManager
├─ entities.py          # 掉落物（吸附拾取）、投射物、粒子、飘字
├─ physics.py           # 轴分离的方块碰撞（玩家/怪物/掉落物共用）
├─ inventory.py         # 背包数据、快捷栏/背包网格/制作面板 UI、物品提示
├─ textures.py          # 程序化像素贴图生成与 PNG 覆盖加载（Assets）
├─ render.py            # 区块表面缓存渲染、边缘描边、背景墙、挖掘裂纹
├─ lighting.py          # 方块分辨率光照图 → 平滑暗度遮罩（日光、火把、动态光源）
├─ minimap.py           # 已探索区块的小地图（M 键缩放）
├─ background.py        # 群系背景图视差绘制
├─ camera.py            # 跟随玩家的视口与坐标转换
├─ healthbar.py         # 右上角生命条
├─ manabar.py           # 生命条下方魔力条
├─ ui.py                # 中文字体加载、文字/按钮/面板/提示框
├─ requirements.txt     # Python 依赖清单（pygame）
├─ images/              # 位图资源
│  ├─ screen_pics/      # 开始界面背景
│  └─ background_pics/  # 各群系/层级背景（12 张 JPG）
├─ tools/
│  └─ smoke_test.py     # 无窗口冒烟测试：模拟键鼠驱动真实游戏循环，29 项检查 + 截图
├─ docs/
│  ├─ PROJECT_STATUS.md # 实现状态、验证结果、风险
│  ├─ ROADMAP.md        # 里程碑（M0/M1 已完成，其余为提案）
│  └─ GAME_DESIGN.md    # 设计简报与竞品调研问题
├─ logs/                # 每次更新的 changelog（目的与影响）
├─ AGENTS.md            # Agent 协作规则与边界
└─ .gitignore           # 忽略缓存、虚拟环境、测试截图（不忽略 images/）
```

只读参考项目（勿修改）：`D:\lab_files\game\PyRarria-master`。

## 运行方式

所有命令都在 PowerShell 中执行，并且必须在**项目根目录**运行（`images/` 使用相对路径）。

### 1. 准备环境

本机已验证的环境：MSYS2 UCRT64 Python 3.14.8 + pygame 2.6.1（通过 pacman 安装，因为这个 Python 不允许 pip 安装，且 pygame 无法从源码编译）：

```powershell
C:\msys64\usr\bin\pacman.exe -S --noconfirm mingw-w64-ucrt-x86_64-python-pygame
```

如果使用 python.org 官方 Python（3.10–3.13，未在本机验证），用虚拟环境 + pip：

```powershell
Set-Location "D:\lab_files\game\py_terraria"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 2. 启动游戏

```powershell
Set-Location "D:\lab_files\game\py_terraria"
python game.py
```

### 3. 运行冒烟测试（无窗口）

```powershell
Set-Location "D:\lab_files\game\py_terraria"
python tools/smoke_test.py
```

最后一行应为 `29/29 checks passed`。截图输出到 `tools/screenshots/`。

## 操作

| 按键 | 作用 |
|------|------|
| A / D | 左右移动（遇到 1 格高台阶自动上跨） |
| 空格 / W | 跳跃（按住跳得更高；水中连按上浮） |
| 鼠标左键（按住） | 使用当前物品：镐挖矿、斧砍树、剑挥砍、放置方块、射箭 / 施法、吃药 |
| 1–0 / 滚轮 | 切换快捷栏 |
| E / Tab | 打开背包与制作界面（左键拿起 / 放下，右键取 1 个；在界面外点击会把手上物品丢出） |
| H | 快速治疗（优先治疗药水，其次蘑菇；10 秒冷却） |
| M | 小地图缩放 |
| Esc | 关闭背包 / 暂停菜单 |

## 进度路线（游戏内）

木材 → 工作台 → 木剑 / 木弓 / 木箭 / 治疗药水 → 石块 + 火把 → 熔炉 → 铜 / 铁 / 金锭 → 铁砧 → 铁 / 金工具与武器 → 金镐开采地狱狱石 → 熔岩镐 / 炽焰巨剑。恶魔眼的晶状体 + 金锭可以做火花法杖，骷髅的骨头可以做骨剑。

## 文档

| 文件 | 用途 |
|------|------|
| [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) | 实现状态、验证结果、风险、未知项 |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | 里程碑（非承诺排期） |
| [`docs/GAME_DESIGN.md`](docs/GAME_DESIGN.md) | 设计原则、Demo 评估、竞品调研问题 |
| [`logs/`](logs/) | 每次更新的变更记录 |

## 贴图替换

所有贴图都在运行时程序化生成。把同名 PNG 放到 `images/textures/tiles/<方块名>.png` 或 `images/textures/items/<物品名>.png`，就会替代对应的生成贴图（名称见 `tiles.py` / `items.py`）。

## 许可与参考

本仓库为原创开发项目，代码与生成贴图均为原创。`PyRarria-master` 仅作只读参考，未复制其代码或资源。注意：`images/screen_pics/start_screen.jpg` 中含有 Terraria 官方标志，若要公开发布，需要替换为原创图片。
