# Changelog — 2026-10-27 让 Python 3.15 能安装并运行 Pygame

原版 pygame 2.6.1 没有 Python 3.15 的 Windows wheel。直接 `pip install pygame` 会下载源码包，并在 `distutils.msvccompiler` 已被移除的构建环境里失败。游戏因此无法在当前官方 Python 上启动。

## 变更

- **运行环境**（新增，已被 `.gitignore` 忽略）：用 `C:\Python315\python.exe` 在项目根目录创建 `.venv`，只安装 `pygame-ce==2.5.8` 的 `cp315-win_amd64` wheel。虚拟环境内的 pip 从 26.2.1 升到 26.2.2。系统 Python、PATH 和游戏源码没有改动。
- **`requirements.txt`**：依赖从 `pygame>=2.5` 改为 `pygame-ce==2.5.8`。目的是让 `pip install -r requirements.txt` 安装有 3.15 wheel 的发行版。pygame-ce 与原版 pygame 都会占用 `pygame` 这个导入目录，不能装在同一个环境里。
- **`README.md`、`docs/PROJECT_STATUS.md`、`AGENTS.md`**：运行和验收命令改为项目虚拟环境的解释器，并写明当前验证过的发行版是 pygame-ce。

## 影响

导入方式不变，现有 `import pygame` 继续有效。运行时链接的是 SDL 2.32.10，而不是原版 2.6.1 预编译包里的 SDL 2.28.4。以后在这台机器上应使用 `.\.venv\Scripts\python.exe`，系统的 `python` 仍然指向没有安装游戏依赖的 `C:\Python315\python.exe`。

## 验证

- `.\.venv\Scripts\python.exe -m pip show pygame-ce`：2.5.8，位于项目 `.venv`。名为 `pygame` 的分发包不存在。
- 导入结果：`pygame.version.ver == 2.5.8`，`pygame.IS_CE == 1`，模块路径在 `.venv\Lib\site-packages\pygame\`。
- `pygame.init()` 创建了 320×180、32 位窗口，`pygame.quit()` 后显示子系统已关闭。
- `.\.venv\Scripts\python.exe tools\smoke_test.py`：**133/133 通过**。地表约 11.1 ms/帧，洞穴约 13.4 ms/帧。
- `game.py` 的桌面试玩没有启动。
