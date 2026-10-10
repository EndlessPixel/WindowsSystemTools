###############################################################################
# Copyright (C) 2024 - 2026 EndlessPixel by system_mini. All rights reserved.
#
# 版权所有 (C) 2024 - 2026 EndlessPixel 由 system_mini 保留所有权利。
###############################################################################
"""系统优化工具 —— 基于 FastUI 的 Web 界面。

界面由 FastUI 声明式组件渲染，所有可执行指令集中维护在 ``commands.json`` 中：
修改该文件即可增删/调整功能，无需改动任何 Python 代码。
"""

from __future__ import annotations

import asyncio
import ctypes
import itertools
import json
import os
import platform
import subprocess
import sys
import threading
import webbrowser
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any

import psutil
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastui import AnyComponent, FastUI, prebuilt_html
from fastui import components as c
from fastui import events as ev
from fastui.forms import fastui_form
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# 应用常量
# ---------------------------------------------------------------------------
APP_NAME = '系统优化工具'
APP_VERSION = 'b2.0'
HOST = '127.0.0.1'
PORT = 8000

COMMANDS_FILE_NAME = 'commands.json'


def _resource_dir() -> Path:
    """代码/内置资源所在目录（PyInstaller onefile 时是临时解压目录）"""
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:
        return Path(meipass)
    return Path(__file__).resolve().parent


def _app_dir() -> Path:
    """可执行文件所在目录，用于存放可编辑的 commands.json"""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def resolve_commands_file() -> Path:
    """定位指令文件：优先用程序目录下的版本，缺失时从内置资源导出一份

    打包成 exe 后，内置指令无法修改；首次启动时把它复制到 exe 同级目录，
    用户即可继续通过编辑 commands.json 增删功能。
    """
    target = _app_dir() / COMMANDS_FILE_NAME
    if target.exists():
        return target

    bundled = _resource_dir() / COMMANDS_FILE_NAME
    if bundled != target and bundled.exists():
        try:
            target.write_bytes(bundled.read_bytes())
            return target
        except OSError:
            return bundled
    return target


BASE_DIR = _app_dir()
COMMANDS_FILE = resolve_commands_file()

COMMAND_TIMEOUT = 600   # 单条命令的最长执行时间（秒）
WAIT_TIMEOUT = 60       # 请求等待命令返回的时间，超时后转入后台继续执行
MAX_LOG_ENTRIES = 100   # 内存中保留的执行日志条数
MAX_OUTPUT_CHARS = 4000  # 单条日志输出的最大字符数


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------
class CommandItem(BaseModel):
    """一条可执行指令"""

    id: str
    name: str
    command: str
    scope: str  # normal / admin
    group_id: str
    group: str


class CommandGroup(BaseModel):
    """一个功能分组"""

    id: str
    name: str
    scope: str  # normal / admin
    items: list[CommandItem]


class LogEntry(BaseModel):
    """一条执行日志"""

    id: int
    time: str
    source: str
    command: str
    status: str
    output: str = ''


class CustomCommand(BaseModel):
    """手动输入的命令"""

    command: str


# ---------------------------------------------------------------------------
# 指令加载（来自 commands.json）
# ---------------------------------------------------------------------------
def load_commands() -> tuple[list[CommandGroup], dict[str, CommandItem], dict[str, CommandGroup]]:
    """读取 commands.json，构建分组列表与 id 索引"""
    if not COMMANDS_FILE.exists():
        raise FileNotFoundError(f'指令文件不存在：{COMMANDS_FILE}')

    raw: dict[str, Any] = json.loads(COMMANDS_FILE.read_text(encoding='utf-8'))

    groups: list[CommandGroup] = []
    items: dict[str, CommandItem] = {}
    group_map: dict[str, CommandGroup] = {}

    for scope, prefix in (('normal', 'n'), ('admin', 'a')):
        for group_index, group_raw in enumerate(raw.get(scope, [])):
            group_id = f'{prefix}{group_index}'
            entries: list[CommandItem] = []

            for item_index, item_raw in enumerate(group_raw.get('items', [])):
                item_id = f'{group_id}-{item_index}'
                item = CommandItem(
                    id=item_id,
                    name=item_raw['name'],
                    command=item_raw['command'],
                    scope=scope,
                    group_id=group_id,
                    group=group_raw['name'],
                )
                entries.append(item)
                items[item_id] = item

            group = CommandGroup(
                id=group_id,
                name=group_raw['name'],
                scope=scope,
                items=entries,
            )
            groups.append(group)
            group_map[group_id] = group

    return groups, items, group_map


GROUPS, COMMANDS, GROUP_MAP = load_commands()


# ---------------------------------------------------------------------------
# 权限检测
# ---------------------------------------------------------------------------
def is_admin() -> bool:
    """判断当前进程是否具有管理员 / root 权限"""
    if os.name == 'nt':
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
    try:
        return os.geteuid() == 0
    except AttributeError:
        return False


# ---------------------------------------------------------------------------
# 执行日志
# ---------------------------------------------------------------------------
_LOG_SEQ = itertools.count(1)
_LOGS: deque[LogEntry] = deque(maxlen=MAX_LOG_ENTRIES)
_LOG_LOCK = threading.Lock()


def _now() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def _clip(text: str) -> str:
    text = (text or '').strip()
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return text[:MAX_OUTPUT_CHARS] + '\n...（输出过长，已截断）'


def _append_log(source: str, command: str, status: str, output: str = '') -> LogEntry:
    entry = LogEntry(
        id=next(_LOG_SEQ),
        time=_now(),
        source=source,
        command=command,
        status=status,
        output=_clip(output),
    )
    with _LOG_LOCK:
        _LOGS.appendleft(entry)
    return entry


def execute_command(source: str, command: str) -> LogEntry:
    """同步执行命令并把结果写入日志，供后台线程调用"""
    entry = _append_log(source, command, '执行中', '')

    try:
        completed = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            errors='replace',
            timeout=COMMAND_TIMEOUT,
        )
        output = completed.stdout or ''
        if completed.stderr:
            output = f'{output}\n[错误输出]\n{completed.stderr}'
        entry.status = '执行成功' if completed.returncode == 0 else f'执行失败（退出码 {completed.returncode}）'
        entry.output = _clip(output) or '（命令没有产生输出）'
    except subprocess.TimeoutExpired:
        entry.status = f'执行超时（超过 {COMMAND_TIMEOUT} 秒）'
        entry.output = '命令已被终止，请拆分为更小的操作后重试。'
    except Exception as exc:  # noqa: BLE001 - 兜底，保证界面可用
        entry.status = '执行异常'
        entry.output = str(exc)

    return entry


async def submit_command(source: str, command: str) -> str:
    """提交命令执行，超时则转入后台继续运行"""
    loop = asyncio.get_running_loop()
    try:
        entry = await asyncio.wait_for(
            loop.run_in_executor(None, execute_command, source, command),
            timeout=WAIT_TIMEOUT,
        )
        return f'“{source}” {entry.status}'
    except asyncio.TimeoutError:
        return f'“{source}” 执行时间较长，已转入后台运行，可在执行日志中查看结果'


# ---------------------------------------------------------------------------
# 界面片段
# ---------------------------------------------------------------------------
def layout(*components: AnyComponent) -> list[AnyComponent]:
    """页面骨架：标题、导航栏、主体内容"""
    return [
        c.PageTitle(text=f'{APP_NAME} · {APP_VERSION}'),
        c.Navbar(
            title=APP_NAME,
            start_links=[
                c.Link(components=[c.Text(text='首页')], on_click=ev.GoToEvent(url='/')),
                c.Link(components=[c.Text(text='执行日志')], on_click=ev.GoToEvent(url='/logs')),
            ],
            end_links=[
                c.Link(
                    components=[c.Text(text='管理员权限：已启用' if is_admin() else '管理员权限：未启用')],
                )
            ],
        ),
        c.Page(
            components=[
                c.Div(class_name='container-fluid py-3', components=list(components)),
            ]
        ),
    ]


def permission_notice() -> AnyComponent:
    """权限提示条"""
    if is_admin():
        return c.Paragraph(
            text='已检测到管理员权限，所有功能均可使用。',
            class_name='alert alert-success mt-3 mb-0',
        )
    return c.Paragraph(
        text='未检测到管理员权限，管理员功能将不可用。如需使用，请以管理员身份重新启动本工具。',
        class_name='alert alert-warning mt-3 mb-0',
    )


def system_info_components() -> list[AnyComponent]:
    """系统状态卡片"""
    cpu = psutil.cpu_percent(interval=0.3)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(os.path.abspath(os.sep))
    net = psutil.net_io_counters()

    cards = [
        ('CPU 使用率', f'{cpu}%'),
        (
            '内存使用率',
            f'{memory.percent}%（{memory.used / 2**30:.1f} / {memory.total / 2**30:.1f} GB）',
        ),
        (
            '磁盘使用率',
            f'{disk.percent}%（剩余 {disk.free / 2**30:.1f} GB）',
        ),
        (
            '网络流量（上传 / 下载）',
            f'{net.bytes_sent / 2**20:.1f} MB / {net.bytes_recv / 2**20:.1f} MB',
        ),
    ]

    return [
        c.Div(
            class_name='row g-3',
            components=[
                c.Div(
                    class_name='col-6 col-md-3',
                    components=[
                        c.Div(
                            class_name='card h-100 shadow-sm',
                            components=[
                                c.Div(
                                    class_name='card-body',
                                    components=[
                                        c.Heading(text=title, level=6, class_name='card-subtitle text-muted mb-2'),
                                        c.Text(text=value),
                                    ],
                                )
                            ],
                        )
                    ],
                )
                for title, value in cards
            ],
        ),
        c.Paragraph(
            text=f'更新时间：{_now()} · 平台：{platform.system()} {platform.release()}',
            class_name='text-muted small mt-2 mb-0',
        ),
    ]


def command_grid(group: CommandGroup) -> list[AnyComponent]:
    """分组内的指令按钮"""
    admin = is_admin()
    buttons: list[AnyComponent] = []

    for item in group.items:
        locked = group.scope == 'admin' and not admin
        buttons.append(
            c.Button(
                text=item.name,
                on_click=None if locked else ev.GoToEvent(url=f'/cmd/{item.id}'),
                named_style='secondary' if locked else 'primary',
                class_name='m-1',
            )
        )

    return [c.Div(class_name='d-flex flex-wrap', components=buttons)]


def group_link_list(scope: str) -> AnyComponent:
    """分组导航列表"""
    links = [
        c.Link(
            components=[c.Text(text=f'{group.name}（{len(group.items)}）')],
            on_click=ev.GoToEvent(url=f'/group/{group.id}'),
        )
        for group in GROUPS
        if group.scope == scope
    ]
    return c.LinkList(links=links, mode='vertical')


def custom_command_form() -> list[AnyComponent]:
    """手动执行命令表单"""
    return [
        c.Heading(text='手动执行命令', level=3, class_name='mt-4'),
        c.Form(
            submit_url='/api/custom/run',
            method='POST',
            form_fields=[
                c.FormFieldInput(
                    name='command',
                    title='命令',
                    placeholder='例如：ipconfig /all',
                    required=True,
                )
            ],
        ),
    ]


def log_components() -> list[AnyComponent]:
    """执行日志列表"""
    with _LOG_LOCK:
        entries = list(_LOGS)

    if not entries:
        return [c.Paragraph(text='暂无执行记录，执行任意命令后结果会显示在这里。')]

    blocks: list[AnyComponent] = []
    for entry in entries:
        blocks.append(
            c.Div(
                class_name='card mb-3 shadow-sm',
                components=[
                    c.Div(
                        class_name='card-body',
                        components=[
                            c.Heading(text=f'#{entry.id} · {entry.source}', level=5, class_name='card-title'),
                            c.Paragraph(
                                text=f'时间：{entry.time} · 状态：{entry.status}',
                                class_name='text-muted small',
                            ),
                            c.Code(text=entry.command, class_name='mb-2'),
                            c.Code(text=entry.output or '（无输出）'),
                        ],
                    )
                ],
            )
        )
    return blocks


# ---------------------------------------------------------------------------
# FastAPI 应用
# ---------------------------------------------------------------------------
app = FastAPI(title=APP_NAME, version=APP_VERSION)


@app.get('/api/', response_model=FastUI, response_model_exclude_none=True)
def index_page() -> list[AnyComponent]:
    """首页：系统状态、手动执行、功能分组导航"""
    return layout(
        c.Heading(text='系统状态', level=3),
        c.Div(
            class_name='mb-3',
            components=[
                c.Button(
                    text='刷新系统信息',
                    on_click=ev.PageEvent(name='refresh-info'),
                    named_style='secondary',
                )
            ],
        ),
        c.ServerLoad(
            path='/system-info',
            load_trigger=ev.PageEvent(name='refresh-info'),
            components=system_info_components(),
        ),
        permission_notice(),
        *custom_command_form(),
        c.Heading(text='功能分组', level=3, class_name='mt-4'),
        c.Div(
            class_name='row',
            components=[
                c.Div(
                    class_name='col-md-6',
                    components=[c.Heading(text='普通功能', level=5), group_link_list('normal')],
                ),
                c.Div(
                    class_name='col-md-6',
                    components=[c.Heading(text='管理员功能', level=5), group_link_list('admin')],
                ),
            ],
        ),
    )


@app.get('/api/system-info', response_model=FastUI, response_model_exclude_none=True)
def system_info_fragment() -> list[AnyComponent]:
    """系统状态片段，供 ServerLoad 局部刷新"""
    return system_info_components()


@app.get('/api/group/{group_id}', response_model=FastUI, response_model_exclude_none=True)
def group_page(group_id: str) -> list[AnyComponent]:
    """分组页：列出该分组下的全部指令"""
    group = GROUP_MAP.get(group_id)
    if group is None:
        raise HTTPException(status_code=404, detail='未找到该功能分组')

    return layout(
        c.Heading(text=group.name, level=3),
        c.Paragraph(
            text=f'共 {len(group.items)} 条指令 · 类型：{"管理员功能" if group.scope == "admin" else "普通功能"}',
            class_name='text-muted',
        ),
        c.Div(
            class_name='mb-3',
            components=[c.Button(text='返回首页', on_click=ev.GoToEvent(url='/'), named_style='secondary')],
        ),
        permission_notice() if group.scope == 'admin' else c.Div(components=[]),
        *command_grid(group),
        *custom_command_form(),
    )


@app.get('/api/cmd/{command_id}', response_model=FastUI, response_model_exclude_none=True)
def command_page(command_id: str) -> list[AnyComponent]:
    """指令确认页"""
    item = COMMANDS.get(command_id)
    if item is None:
        raise HTTPException(status_code=404, detail='未找到该指令')

    locked = item.scope == 'admin' and not is_admin()

    body: list[AnyComponent] = [
        c.Heading(text=item.name, level=3),
        c.Paragraph(
            text=f'所属分组：{item.group} · 类型：{"管理员功能" if item.scope == "admin" else "普通功能"}',
            class_name='text-muted',
        ),
        c.Code(text=item.command, class_name='my-3'),
    ]

    if locked:
        body.append(
            c.Paragraph(
                text='当前未以管理员身份运行，该指令不可用。请以管理员身份重新启动本工具。',
                class_name='alert alert-danger',
            )
        )
    else:
        body.append(c.Paragraph(text='确认无误后提交表单即可执行，执行结果可在“执行日志”中查看。'))
        body.append(
            c.Form(
                submit_url=f'/api/cmd/{item.id}/run',
                method='POST',
                form_fields=[
                    c.FormFieldInput(name='confirm', title='', html_type='hidden', initial='1')
                ],
            )
        )

    body.append(
        c.Div(
            class_name='mt-3 d-flex gap-2',
            components=[
                c.Button(text='返回分组', on_click=ev.GoToEvent(url=f'/group/{item.group_id}'), named_style='secondary'),
                c.Button(text='返回首页', on_click=ev.GoToEvent(url='/'), named_style='secondary'),
            ],
        )
    )

    return layout(*body)


@app.post('/api/cmd/{command_id}/run', response_model=FastUI, response_model_exclude_none=True)
async def run_command(command_id: str) -> list[AnyComponent]:
    """执行内置指令"""
    item = COMMANDS.get(command_id)
    if item is None:
        raise HTTPException(status_code=404, detail='未找到该指令')

    if item.scope == 'admin' and not is_admin():
        _append_log(item.name, item.command, '已拒绝', '缺少管理员权限，命令未执行。')
        return [c.FireEvent(event=ev.GoToEvent(url='/logs'), message='缺少管理员权限，命令未执行')]

    message = await submit_command(item.name, item.command)
    return [c.FireEvent(event=ev.GoToEvent(url='/logs'), message=message)]


@app.post('/api/custom/run', response_model=FastUI, response_model_exclude_none=True)
async def run_custom_command(form: Annotated[CustomCommand, fastui_form(CustomCommand)]) -> list[AnyComponent]:
    """执行手动输入的命令"""
    command = form.command.strip()
    if not command:
        return [c.FireEvent(event=ev.GoToEvent(url='/'), message='请输入要执行的命令')]

    message = await submit_command('自定义命令', command)
    return [c.FireEvent(event=ev.GoToEvent(url='/logs'), message=message)]


@app.get('/api/logs', response_model=FastUI, response_model_exclude_none=True)
def logs_page() -> list[AnyComponent]:
    """执行日志页"""
    return layout(
        c.Heading(text='执行日志', level=3),
        c.Div(
            class_name='mb-3',
            components=[
                c.Button(
                    text='刷新日志',
                    on_click=ev.PageEvent(name='refresh-logs'),
                    named_style='secondary',
                )
            ],
        ),
        c.ServerLoad(
            path='/logs/content',
            load_trigger=ev.PageEvent(name='refresh-logs'),
            components=log_components(),
        ),
    )


@app.get('/api/logs/content', response_model=FastUI, response_model_exclude_none=True)
def logs_fragment() -> list[AnyComponent]:
    """日志片段，供 ServerLoad 局部刷新"""
    return log_components()


@app.get('/{path:path}', include_in_schema=False)
async def html_page() -> HTMLResponse:
    """所有页面入口：返回 FastUI 前端 HTML"""
    return HTMLResponse(prebuilt_html(title=f'{APP_NAME} · {APP_VERSION}'))


# ---------------------------------------------------------------------------
# 启动入口
# ---------------------------------------------------------------------------
def main() -> None:
    import uvicorn

    print(f'{APP_NAME} 已启动：http://{HOST}:{PORT}')
    print('EndlessPixel by system_mini')
    print(f'版本信息：{APP_VERSION}')
    print(f'已加载指令：{len(COMMANDS)} 条 / 分组 {len(GROUPS)} 个')
    print(f'指令文件：{COMMANDS_FILE}')
    print('感谢您的使用！')

    threading.Timer(1.0, lambda: webbrowser.open(f'http://{HOST}:{PORT}')).start()
    uvicorn.run(app, host=HOST, port=PORT, log_level='info')


if __name__ == '__main__':
    main()
