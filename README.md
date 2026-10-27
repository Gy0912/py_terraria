# PyTerraria

早期阶段的 2D 沙盒生存冒险游戏（Python + Pygame）。玩法以 Terraria 为主要参考，同时借鉴了《我的世界》、《星露谷物语》和自动化建造类游戏的机制，目标是逐步形成原创组合。项目处于积极开发中。

## 当前状态（v0.3.0）

- **世界**：6400×1800 格，每格 16 像素（玩家宽 1.5 格），按 32×32 区块懒加载。五种地表群系，分为地表、地下、洞穴、地狱四层，另有浮空岛。有背景墙层，水和岩浆会流动，二者相遇会生成黑曜石。
- **特殊建筑（9 种）**：森林木屋、地下木屋、矿井、沙漠金字塔（困着可解救的传送师）、雪原冰屋、丛林遗迹、海底沉船、浮空岛、地狱塔，每座都有一个带专属战利品的宝箱。
- **生存**：水下有氧气条，耗尽会窒息掉血；接触岩浆会持续燃烧；高处坠落有伤害；跳跃高度约 5.5 格。
- **装备**：头 / 身 / 腿三件盔甲（铜、铁、金、熔岩四套，外观会显示在角色身上）和 5 个饰品栏（疾风靴、云中瓶、潜水面罩、黑曜石护符、磁力戒指等 10 种）。
- **NPC**：向导、商人、护士、传送师、铁匠。用"封闭房间 + 背景墙 + 门 + 光源 + 床"建房后，NPC 会按条件入住；可以对话、购买、出售、治疗，以及通过传送晶塔传送。
- **Boss**：血瞳巨眼（夜晚使用召唤物，或满足条件后在夜晚自然出现）和史莱姆之王（使用召唤物，或在史莱姆雨中击杀 40 只史莱姆后出现）。击败后掉落宝藏袋，内含专属饰品。
- **跨作品机制**：床可以设置重生点，夜晚还能睡觉跳过（我的世界）；水桶 / 岩浆桶（我的世界）；出货箱第二天早上自动结算（星露谷）；磁力戒指（星露谷）；自动熔炉（自动化游戏）；死亡掉落一半金币。
- **存档**：开始游戏后进入世界选择界面，共 3 个存档位，可以新建、读取、删除；暂停菜单可以保存，每 3 分钟自动保存一次。
- 详情见 [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md)。

## 项目结构

```
py_terraria/
├─ game.py              # 入口；Game：会话、主循环、昼夜事件、睡觉、交易、HUD 与界面编排
├─ menus.py             # 世界选择界面（存档位、新建 / 读取 / 删除、名称与种子输入）
├─ save.py              # 存档读写：只保存改动过的区块（zlib+base64），附方块名称表以兼容旧档
├─ settings.py          # 屏幕、16px 方块、世界尺寸与分层行号、昼夜、氧气、存档参数、中文名
├─ tiles.py             # 方块注册表（含多格物体尺寸、门对怪物的阻挡）与背景墙注册表
├─ items.py             # 物品（方块/墙/工具/武器/盔甲/饰品/袋子/召唤物/桶）、配方、售价、战利品表
├─ worldgen.py          # 基于种子的噪声地形、背景墙、水池 / 岩浆、陶罐与生命水晶、树木、建筑叠加
├─ structures.py        # 9 种特殊建筑的蓝图与全图规划、宝箱战利品
├─ world.py             # 区块（方块 / 墙 / 水位三层）、多格物体与容器、液体流动模拟、改动追踪
├─ player.py            # 玩家物理、装备属性汇总、氧气 / 燃烧 / 跌落、二段跳、重生点、盔甲外观
├─ actions.py           # 物品使用：挖掘、砍树、敲墙、放置方块 / 物体 / 墙、桶、袋子、召唤、魔镜、右键交互
├─ creatures.py         # 怪物类型与三类 AI、按环境刷怪、史莱姆雨
├─ bosses.py            # 血瞳巨眼、史莱姆之王、Boss 管理器、宝藏袋
├─ npc.py               # NPC 类型、入住条件、房屋检测、游荡 AI、解救
├─ panels.py            # NPC 对话面板、传送晶塔面板
├─ inventory.py         # 背包、装备栏、制作 / 箱子 / 商店面板、通用格子操作
├─ entities.py          # 掉落物（磁力吸附）、投射物、粒子、飘字
├─ physics.py           # 方块碰撞（玩家与怪物两套判定）、液体检测
├─ textures.py          # 程序化像素贴图：方块、物体、背景墙、图标、玩家盔甲外观、NPC、Boss
├─ render.py            # 区块缓存（墙 + 方块）、液体缓存、物体与裂纹绘制
├─ lighting.py          # 32px 网格光照：日光、火把、动态光源（头灯、火球、发光怪物）
├─ minimap.py           # 已探索区域小地图（含 NPC / Boss 标记）
├─ background.py        # 群系背景图视差
├─ camera.py            # 跟随视口
├─ healthbar.py         # 生命条
├─ manabar.py           # 魔力条
├─ ui.py                # 中文字体、文字、按钮、面板、提示框
├─ requirements.txt     # Python 依赖（pygame-ce；导入名仍是 pygame）
├─ images/
│  ├─ screen_pics/      # 开始界面背景
│  └─ background_pics/  # 群系 / 层级背景（12 张 JPG）
├─ tools/
│  └─ smoke_test.py     # 无窗口冒烟测试：133 项检查 + 截图（存档写入临时目录）
├─ docs/
│  ├─ PROJECT_STATUS.md # 实现状态、验证结果、风险
│  ├─ ROADMAP.md        # 里程碑
│  └─ GAME_DESIGN.md    # 设计简报、借鉴机制、竞品调研问题
├─ logs/                # 每次更新的 changelog
├─ AGENTS.md            # Agent 协作规则
└─ .gitignore           # 忽略缓存、虚拟环境、测试截图、saves/
```

运行时会在项目根目录生成 `saves/`（存档）和 `.venv/`（虚拟环境）。二者都不纳入版本控制。只读参考项目（勿修改）：`D:\lab_files\game\PyRarria-master`。

## 运行方式

所有命令都在 PowerShell 中执行，并且必须在**项目根目录**运行。

### 1. 准备环境

当前已验证的环境是 python.org 的 Python 3.15.0 加项目虚拟环境里的 pygame-ce 2.5.8。系统 Python 的 `site-packages` 不可写，原版 pygame 2.6.1 也没有 Python 3.15 的 Windows wheel，所以依赖只装在 `.venv` 里。`.venv/` 已被 `.gitignore` 忽略。

```powershell
Set-Location "D:\lab_files\game\py_terraria"
& "C:\Python315\python.exe" -m venv ".\.venv"
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

安装日志应出现 `pygame_ce-2.5.8-cp315-cp315-win_amd64.whl`。确认实际加载的是 pygame-ce：

```powershell
.\.venv\Scripts\python.exe -c "import pygame; print(pygame.version.ver, pygame.IS_CE, pygame.__file__)"
```

预期：`2.5.8 1`，并且路径位于 `.venv\Lib\site-packages\pygame\`。

### 2. 启动游戏

```powershell
Set-Location "D:\lab_files\game\py_terraria"
.\.venv\Scripts\python.exe game.py
```

点击"开始游戏"后进入世界选择界面：在空存档位点击"新建世界"（可以输入名称和种子），或在已有存档上点击"进入游戏"。

### 3. 运行冒烟测试（无窗口）

```powershell
Set-Location "D:\lab_files\game\py_terraria"
.\.venv\Scripts\python.exe tools\smoke_test.py
```

最后一行应为 `133/133 checks passed`。截图输出到 `tools/screenshots/`。

## 操作

| 按键 | 作用 |
|------|------|
| A / D | 左右移动（遇到 1 格高台阶自动上跨） |
| 空格 / W | 跳跃（按住跳得更高；装备云中瓶后可在空中二段跳；水中连按上浮） |
| 鼠标左键（按住） | 使用当前物品：挖掘 / 砍树 / 敲墙 / 攻击 / 放置 / 射击 / 喝药 / 开袋 / 召唤 |
| 鼠标右键 | 与 NPC 对话；打开箱子 / 出货箱 / 自动熔炉；用床设重生点或睡觉；使用传送晶塔 |
| 1–0 / 滚轮 | 切换快捷栏 |
| E / Tab | 打开背包、装备栏、制作界面（Shift+左键：快速装备、存取或出售） |
| H | 快速治疗 |
| M | 小地图缩放 |
| Esc | 关闭界面 / 暂停（暂停菜单可保存） |

## 游戏流程提示

1. 砍树 → 工作台 → 木锤、门、床、木墙 → 盖出第一间房，向导会入住。
2. 挖矿 → 熔炉 → 金属锭 → 铁砧 → 盔甲、工具和水桶；持有 50 金币并准备好空房后，商人会到来。
3. 探索建筑寻找饰品；在沙漠金字塔里解救传送师，之后可以用传送晶塔在各地之间传送。
4. 用 6 个晶状体做可疑眼球，在夜晚召唤血瞳巨眼；或者等史莱姆雨，击杀 40 只史莱姆引出史莱姆之王。击败任意 Boss 后铁匠会到来。
5. 用金镐开采狱石，制作熔岩装备；在岩浆旁边用水桶倒水得到黑曜石，再做成黑曜石护符来抵御岩浆。

## 文档

| 文件 | 用途 |
|------|------|
| [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) | 实现状态、验证结果、风险 |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | 里程碑 |
| [`docs/GAME_DESIGN.md`](docs/GAME_DESIGN.md) | 设计简报、借鉴机制、竞品调研 |
| [`logs/`](logs/) | 每次更新的变更记录 |

## 贴图替换

所有贴图都在运行时程序化生成。把同名 PNG 放到 `images/textures/tiles/<方块名>.png` 或 `images/textures/items/<物品名>.png`，就会替代对应的生成贴图（多格物体按整体尺寸缩放）。

## 许可与参考

本仓库为原创开发项目，代码与生成贴图均为原创。`PyRarria-master` 仅作只读参考，未复制其代码或资源。`images/screen_pics/start_screen.jpg` 中含有 Terraria 官方标志，若要公开发布，需要替换为原创图片。
