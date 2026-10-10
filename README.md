# WindowsSystemTools

![Version](https://img.shields.io/badge/version-b2.0-orange)
![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Windows-blue?logo=windows&logoColor=white)
![FastUI](https://img.shields.io/badge/UI-FastUI-009688?logo=fastapi&logoColor=white)
![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688?logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Stars](https://img.shields.io/github/stars/EndlessPixel/WindowsSystemTools?style=flat&color=gold)

一个用 **FastUI（FastAPI）** 重写的 Windows 系统快捷管理工具：浏览器打开即用，所有指令集中维护在 `commands.json`，改 JSON 就能增删功能，不用碰代码。

## 特性

- **Web 界面**：FastUI 声明式组件渲染，无需打包桌面客户端
- **指令外置**：226 条内置指令全部放在 `commands.json`，可自由增删改
- **分组浏览**：普通功能 9 组 / 管理员功能 16 组，按分组查看与执行
- **确认后执行**：每条指令先展示完整命令，确认后才执行，避免误触
- **执行日志**：记录命令、状态、输出与耗时，可随时刷新查看
- **手动执行**：内置输入框，任意命令即输即跑
- **系统状态**：CPU / 内存 / 磁盘 / 网络实时查看，支持手动刷新
- **权限检测**：未以管理员身份运行时自动禁用管理员功能

内置分组涵盖远程桌面管理、安全防护开关、系统服务启停、系统清理优化、进程管理、启动项设置、网络配置、Windows 更新管理、时区与时间同步、视觉效果调整、安全扫描、系统还原点、电源管理、用户与权限、日志与事件等。

## 快速开始

```bash
pip install -r requirements.txt
python main.py
```

启动后自动打开 <http://127.0.0.1:8000>，也可手动访问。Windows 下双击 `start.bat` 即可。

如需使用管理员功能，请右键 `start.bat` → **以管理员身份运行**，否则管理员分组会被禁用。

> FastUI 前端资源默认从 jsDelivr CDN 加载，首次使用需要联网。

## 使用说明

1. **首页**：查看系统状态、手动执行命令、进入功能分组
2. **分组页**：点击指令按钮进入确认页
3. **确认页**：核对命令内容，提交后执行，自动跳转到执行日志
4. **执行日志**：查看每条命令的状态与输出，支持刷新

命令在后台线程执行：60 秒内返回结果，超时则转入后台继续运行，结果同样写入日志；单条命令最长执行 600 秒。

## 指令配置

`commands.json` 是唯一的指令来源：

```json
{
  "version": 1,
  "normal": [
    {
      "name": "系统工具",
      "items": [
        { "name": "打开任务管理器", "command": "start taskmgr" }
      ]
    }
  ],
  "admin": [
    {
      "name": "远程与连接",
      "items": [
        { "name": "启用远程桌面", "command": "reg add ... /f" }
      ]
    }
  ]
}
```

| 字段 | 说明 |
| --- | --- |
| `normal` | 普通功能分组，无需管理员权限 |
| `admin` | 管理员功能分组，需以管理员身份运行 |
| `name` | 分组或指令的显示名称 |
| `items` | 分组下的指令列表 |
| `command` | 实际执行的命令，通过系统 shell 执行 |

新增指令只需在对应分组的 `items` 中追加对象，重启服务即生效。

## 目录结构

```
main.py          # FastUI 界面、指令加载、命令执行与执行日志
commands.json    # 全部指令数据
requirements.txt # 依赖清单
start.bat        # Windows 一键启动
```

## 环境要求

- Python 3.10+
- FastAPI / Uvicorn / FastUI / psutil
- Windows（指令本身面向 Windows，其他系统仅可作演示）

## 说明

本工具为个人学习项目，仅用于快捷执行系统命令，请谨慎执行任何修改系统配置的指令。
专业场景建议使用 Dism++ 等成熟工具。

## 许可

见 [LICENSE](./LICENSE)。
