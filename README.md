# WindowsSystemTools

一个基于 **FastUI（FastAPI）** 的 Windows 系统快捷管理工具，浏览器打开即用。
所有可执行指令集中维护在 [`commands.json`](./commands.json) 中，改 JSON 即可增删功能，无需改动 Python 代码。

## 简介

集成了常用的 Windows 系统管理命令，方便一键执行操作，自用、学习、娱乐均可。
界面由 FastUI 声明式组件渲染，后端负责加载指令、执行命令并记录执行日志。

## 功能

- 系统状态实时查看（CPU / 内存 / 磁盘 / 网络）
- 普通功能与管理员功能分组浏览
- 单条指令确认后执行，执行结果写入执行日志
- 手动输入命令执行
- 管理员权限检测，非管理员自动禁用管理员功能

内置分组包括：远程桌面管理、安全防护开关、系统服务启停、系统清理优化、进程管理、
启动项设置、网络配置、Windows 更新管理、时区/时间同步、视觉效果调整、安全扫描、
系统还原点创建等。

## 运行

```bash
pip install -r requirements.txt
python main.py
```

启动后会自动打开 <http://127.0.0.1:8000>；也可手动访问，或双击 `start.bat`。

> 说明：FastUI 前端资源默认从 jsDelivr CDN 加载，首次使用需要联网。
> 需要管理员功能时，请以管理员身份运行（右键 → 以管理员身份运行 `start.bat`）。

## 指令配置（commands.json）

指令全部存放在 `commands.json`，结构如下：

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
  "admin": []
}
```

- `normal`：普通功能分组；`admin`：需要管理员权限的分组。
- `name`：分组 / 指令名称；`command`：实际执行的命令（通过 shell 执行）。
- 新增分组或指令只需在对应数组中追加对象，重启服务即可生效。

## 目录结构

```
main.py          # FastUI 界面 + 命令执行 + 执行日志
commands.json    # 全部指令数据
requirements.txt # 依赖
start.bat        # Windows 一键启动
```

## 说明

本工具为个人学习项目，仅用于快捷执行系统命令。
专业场景请使用 Dism++ 等成熟工具。

## 运行环境

- Python 3.10+
- FastAPI / Uvicorn / FastUI
- psutil
