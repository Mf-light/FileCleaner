# 文件清理工具 (FileCleaner)

一个 Windows 平台自动化文件清理工具，使用 Python + PyQt6 开发。支持自动定时清理过期文件，最小化到系统托盘运行。

## 功能特性

| 特性 | 说明 |
|------|------|
| 自定义目录 | 输入或浏览选择要监控清理的目录路径 |
| 保留天数 | 支持 1 / 3 / 7 / 14 天，超期文件自动清理 |
| 自动定时清理 | 开启后按设定间隔自动执行，无需手动操作 |
| 灵活间隔 | 支持 1 天 / 7 天 / 15 天 / 30 天四种频率 |
| 系统托盘 | 关闭窗口后最小化到托盘，单击图标恢复窗口 |
| 开机自启 | 一键设置开机自启动 |
| 单实例运行 | 防止重复打开，已运行时自动提示 |
| 详细日志 | 实时记录扫描、删除等操作详情 |

## 安装使用

### 方式一：安装包运行 (推荐)

双击 `dist\FileCleaner_Setup.exe` 安装：

1. **欢迎页** → 点击"下一步"
2. **选择目录** → 默认 `C:\Program Files\FileCleaner`，可自定义修改
3. **组件选择** → 勾选"创建桌面快捷方式"（**默认已勾选**）
4. **安装中** → 等待进度完成
5. **完成页面** → 勾选"运行 FileCleaner"直接启动

> 卸载：通过 Windows "设置 → 应用" 或安装目录下的 `Uninstall.exe` 即可完全卸载。

### 方式二：源码运行

```bash
# 创建虚拟环境并安装依赖
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# 运行程序
.venv\Scripts\python main.py
```

## 界面说明

```
┌─────────────────────────────────────────────────────┐
│  目标目录: [_______________] [浏览] [保存配置]       │
│  保留天数: [7 ▼]   超过选定天数的文件将被删除         │
│                                                     │
│  ☑ 删除前确认    ☑ 开机自启动                        │
│                                                     │
│        [开启清理] 间隔: [7天 ▼] (自动清理频率)       │
│                                                     │
│  操作日志                                           │
│  ┌───────────────────────────────────────────────┐  │
│  │ [2025-05-19 15:00] [INFO] 扫描完成 ...        │  │
│  └───────────────────────────────────────────────┘  │
│                                              就绪    │
└─────────────────────────────────────────────────────┘
```

### 托盘操作

| 操作 | 效果 |
|------|------|
| **单击** 托盘图标 | 显示 / 隐藏主窗口 |
| **右键** 托盘图标 | 弹出菜单：显示窗口 / 退出程序 |
| **点击关闭按钮 (×)** | 隐藏到托盘（不退出），需通过托盘右键退出 |

## 配置说明

程序首次运行会在 exe 同级目录生成 `config.ini`：

```ini
[Settings]
directory_path = C:\zl_robot\input
retention_days = 7
confirm_before_delete = False
auto_start = False
auto_clean_enabled = False
auto_clean_interval = 7
```

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `directory_path` | 要清理的目标目录 | `C:\zl_robot\input` |
| `retention_days` | 文件保留天数 | `7` |
| `confirm_before_delete` | 手动模式下删除前是否弹确认框 | `False` |
| `auto_start` | 是否开机自启 | `False` |
| `auto_clean_enabled` | 是否启用自动清理 | `False` |
| `auto_clean_interval` | 自动清理间隔（天） | `7` |

> 安装包方式部署时，配置和日志均位于**安装目录**下（如 `C:\Program Files\FileCleaner\config.ini`）。

## 构建打包

### 前置条件

- Python 3.12+
- NSIS 3.x（用于制作安装包）：[下载地址](https://nsis.sourceforge.io/Download)
- 或通过 winget 安装：`winget install NSIS.NSIS`

### 第一步：PyInstaller 打包

```bash
# 清理旧构建产物
Remove-Item -Recurse -Force build, dist/FileCleaner -ErrorAction SilentlyContinue

# 打包为目录模式 (onedir)
pyinstaller main.spec
```

产物位于 `dist\FileCleaner\`（包含 FileCleaner.exe 及依赖）。

### 第二步：制作安装包

```bash
"C:\Program Files (x86)\NSIS\makensis.exe" install.nsi
```

最终产物：**`dist\FileCleaner_Setup.exe`** — 标准 Windows 安装程序。

## 项目结构

```
FileCleaner/
├── main.py              # 程序入口、资源路径处理
├── main_window.py       # 主界面 UI、托盘图标、自动清理定时器
├── config_manager.py    # config.ini 读写管理（路径跟随 exe 目录）
├── file_operations.py   # 文件扫描与删除逻辑
├── logger.py            # 日志模块（输出到 exe 同级目录）
├── single_instance.py   # QSharedMemory 单实例检测
├── autostart_manager.py # Windows 注册表开机自启
├── main.spec            # PyInstaller onedir 打包配置
├── install.nsi          # NSIS 安装脚本（含桌面快捷方式选项）
├── config.ini           # 运行时生成的用户配置
├── requirements.txt     # Python 依赖列表
└── resources/
    └── app.ico          # 应用图标
```

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.12+ | 核心语言 |
| PyQt6 | 6.11+ | 图形界面 + 系统托盘 |
| PyInstaller | 6.x | exe 打包 (onedir) |
| NSIS | 3.x | Windows 安装包制作 |
| pywin32 | - | 桌面快捷方式 / 注册表操作 |

## 注意事项

1. **删除不可恢复** — 请谨慎配置目标目录和保留天数，建议先用小目录测试
2. **关闭 ≠ 退出** — 点 × 是隐藏到托盘，真正退出需通过托盘右键菜单
3. **单实例限制** — 同时只能运行一个程序实例
4. **日志位置** — `app.log` 位于程序/安装同级目录，最大 10MB 自动轮转
