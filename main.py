###############################################################################
# Copyright (C) 2024 - 2026 EndlessPixel by system_mini. All rights reserved.
#
# 版权所有 (C) 2024 - 2026 EndlessPixel 由 system_mini 保留所有权利。
###############################################################################

import sys, os, subprocess, ctypes, psutil, threading, winreg
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QTextEdit, QGridLayout, QLabel, QMessageBox, QLineEdit, QTabWidget, QSizePolicy, QSplitter, QStyleFactory
from PyQt5.QtCore import Qt, QTimer, Q_ARG, QMetaObject, pyqtSignal
from PyQt5.QtGui import QIcon

# 在 QApplication 创建之前设置高 DPI 缩放属性
if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

# 检查是否以管理员身份运行
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# 执行 Shell 命令并输出到日志
def run_command(command, log_widget):
    def execute():
        def append_text(text):
            log_widget.append(text)

        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            # 使用 HTML 格式设置命令显示为蓝色
            QMetaObject.invokeMethod(log_widget, "append", Qt.QueuedConnection,
                                     Q_ARG(str, f'<span style="color: blue;">PS C:\\Windows\\System32 > {command}</span>'))
            QMetaObject.invokeMethod(log_widget, "append", Qt.QueuedConnection, Q_ARG(str, ''))
            # 使用 HTML 格式设置标准输出为黑色
            QMetaObject.invokeMethod(log_widget, "append", Qt.QueuedConnection,
                                     Q_ARG(str, f'<span style="color: black;">{result.stdout}</span>'))
            # 使用 HTML 格式设置成功信息为绿色
            QMetaObject.invokeMethod(log_widget, "append", Qt.QueuedConnection,
                                     Q_ARG(str, '<span style="color: green;">命令执行成功</span>'))
            print("命令执行成功")
            QMetaObject.invokeMethod(log_widget, "append", Qt.QueuedConnection, Q_ARG(str, ''))
        except subprocess.CalledProcessError as e:
            # 使用 HTML 格式设置命令显示为蓝色
            QMetaObject.invokeMethod(log_widget, "append", Qt.QueuedConnection,
                                     Q_ARG(str, f'<span style="color: blue;">PS C:\\Windows\\System32 > {command}</span>'))
            QMetaObject.invokeMethod(log_widget, "append", Qt.QueuedConnection, Q_ARG(str, ''))
            # 使用 HTML 格式设置错误信息为红色
            QMetaObject.invokeMethod(log_widget, "append", Qt.QueuedConnection,
                                     Q_ARG(str, f'<span style="color: red;">{e.stderr}</span>'))
            # 使用 HTML 格式设置失败信息为红色
            QMetaObject.invokeMethod(log_widget, "append", Qt.QueuedConnection,
                                     Q_ARG(str, '<span style="color: red;">命令执行失败</span>'))
            print("命令执行失败")
            QMetaObject.invokeMethod(log_widget, "append", Qt.QueuedConnection, Q_ARG(str, ''))
            QMetaObject.invokeMethod(log_widget, "append", Qt.QueuedConnection,
                                     Q_ARG(str, '<span style="color: red;">请检查:</span>'))
            QMetaObject.invokeMethod(log_widget, "append", Qt.QueuedConnection,
                                     Q_ARG(str, '<span style="color: red;"> · 命令是否正确</span>'))
            QMetaObject.invokeMethod(log_widget, "append", Qt.QueuedConnection,
                                     Q_ARG(str, '<span style="color: red;"> · 权限是否足够</span>'))
            QMetaObject.invokeMethod(log_widget, "append", Qt.QueuedConnection,
                                     Q_ARG(str, '<span style="color: red;"> · 系统环境是否配置正确</span>'))
            QMetaObject.invokeMethod(log_widget, "append", Qt.QueuedConnection,
                                     Q_ARG(str, '<span style="color: red;"> · 系统版本是否支持 </span>'))
            QMetaObject.invokeMethod(log_widget, "append", Qt.QueuedConnection,
                                     Q_ARG(str, '<span style="color: red;"> · 文件是否完整</span>'))
            QMetaObject.invokeMethod(log_widget, "append", Qt.QueuedConnection,
                                     Q_ARG(str, '<span style="color: red;"> · 其他可能的错误</span>'))
        except Exception as e:
            QMetaObject.invokeMethod(log_widget, "append", Qt.QueuedConnection,
                                     Q_ARG(str, f'<span style="color: red;">发生未知错误: {str(e)}</span>'))

    # 在新线程中执行命令
    thread = threading.Thread(target=execute)
    thread.start()

# 确认对话框
def confirm_action(parent, message):
    reply = QMessageBox.question(parent, '确认', message, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    return reply == QMessageBox.Yes

# 主窗口类
class SystemOptimizer(QMainWindow):
    def __init__(self):
        super().__init__()
        # 设置窗口图标
        icon_path = "app_icon.ico"  # 图标文件路径，确保图标文件和脚本在同一目录下
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"图标文件 {icon_path} 不存在，请检查路径。")

        self.setWindowTitle("系统优化工具")
        self.resize(800, 450)

        # 设置全局字体大小
        font = self.font()
        font.setPointSize(10)  # 可根据实际情况调整字体大小
        self.setFont(font)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QVBoxLayout(main_widget)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setAcceptRichText(True)
        # 指定可用字体并设置字体大小
        font = self.log_text.font()
        font.setFamily("Microsoft YaHei")
        font.setPointSize(10)  # 可根据实际情况调整字体大小
        self.log_text.setFont(font)

        self.tab_widget = QTabWidget()

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.log_text)
        splitter.addWidget(self.tab_widget)

        splitter.setSizes([200, 400])

        main_layout.addWidget(splitter)

        # 定义普通功能分组
normal_function_groups = {
    "系统工具": [
        ("打开任务管理器", "start taskmgr"),
        ("打开事件查看器", "start eventvwr"),
        ("打开注册表编辑器", "start regedit"),
        ("打开系统信息", "start msinfo32"),
        ("打开控制面板", "start control"),
        ("打开任务计划程序", "start taskschd.msc"),
        ("打开性能监视器", "start perfmon.msc"),
        ("打开计算机管理", "start compmgmt.msc"),
        ("打开本地用户和组", "start lusrmgr.msc"),
        ("打开组策略编辑器", "start gpedit.msc"),
        ("打开磁盘清理", "start cleanmgr"),
        ("打开资源监视器", "start resmon"),
        ("打开系统配置(MSConfig)", "start msconfig"),
        ("打开DirectX诊断工具", "start dxdiag"),
        ("打开组件服务", "start dcomcnfg"),
        ("打开ODBC数据源(64位)", "start odbcad32"),
        ("打开Windows内存诊断", "start mdsched"),
        ("打开打印管理", "start printmanagement.msc"),
        ("打开证书管理", "start certmgr.msc"),
        ("打开本地安全策略", "start secpol.msc"),
    ],

    "资源管理": [
        ("打开文件资源管理器", "start explorer"),
        ("打开磁盘管理", "start diskmgmt.msc"),
        ("打开设备管理器", "start devmgmt.msc"),
        ("打开服务管理器", "start services.msc"),
        ("打开存储感知", "start ms-settings:storagesense"),
        ("打开应用和功能", "start ms-settings:appsfeatures"),
        ("打开任务栏设置", "start ms-settings:taskbar"),
        ("打开磁盘碎片整理", "start dfrgui"),
        ("打开共享文件夹管理", "start fsmgmt.msc"),
        ("打开可靠性和历史记录", "start control /name Microsoft.ReliabilityMonitor"),
        ("打开系统属性", "start sysdm.cpl"),
        ("打开环境变量设置", "powershell rundll32 sysdm.cpl,EditEnvironmentVariables"),
    ],

    "网络与安全": [
        ("打开网络连接", "start ncpa.cpl"),
        ("打开防火墙设置", "start firewall.cpl"),
        ("打开用户账户控制设置", "start ms-settings:uac"),
        ("打开 Windows 安全中心", "start ms-settings:windowsdefender"),
        ("打开网络状态", "start ms-settings:network-status"),
        ("打开 Wi-Fi 设置", "start ms-settings:network-wifi"),
        ("打开 VPN 设置", "start ms-settings:network-vpn"),
        ("打开蓝牙设置", "start ms-settings:bluetooth"),
        ("打开代理设置", "start ms-settings:network-proxy"),
        ("打开数据使用量", "start ms-settings:datausage"),
        ("打开网络重置", "start ms-settings:network-reset"),
        ("打开Windows Defender防火墙高级设置", "start wf.msc"),
        ("打开远程桌面设置", "start ms-settings:remotedesktop"),
        ("打开BitLocker设置", "start control /name Microsoft.BitLockerDriveEncryption"),
        ("刷新DNS缓存", "powershell Clear-DnsClientCache"),
        ("查看IP配置", "powershell ipconfig /all"),
        ("测试网络连通性(谷歌)", "powershell ping 8.8.8.8"),
    ],

    "命令交互": [
        ("打开命令提示符", "start cmd"),
        ("打开 Windows PowerShell", "start powershell"),
        ("打开 Windows PowerShell(管理员)", "powershell Start-Process powershell -Verb RunAs"),
        ("打开命令提示符(管理员)", "powershell Start-Process cmd -Verb RunAs"),
        ("打开 Windows Terminal", "wt"),
        ("打开 Windows Terminal(管理员)", "powershell Start-Process wt -Verb RunAs"),
        ("打开Python交互环境", "start python"),
        ("打开Node.js交互环境", "start node"),
    ],

    "多媒体工具": [
        ("打开计算器", "start calc"),
        ("打开画图", "start mspaint"),
        ("打开记事本", "start notepad"),
        ("打开截图工具", "start snippingtool"),
        ("打开屏幕录制", "start xboxapp:record"),
        ("打开相机", "start microsoft.windows.camera:"),
        ("打开照片应用", "start ms-photos:"),
        ("打开媒体播放器", "start mplay32"),
        ("打开音量混合器", "start sndvol"),
        ("打开声音控制面板", "start mmsys.cpl"),
        ("打开显示颜色校准", "start dccw"),
    ],

    "系统设置": [
        ("打开显示设置", "start ms-settings:display"),
        ("打开声音设置", "start ms-settings:sound"),
        ("打开电源选项", "start control powercfg.cpl"),
        ("打开日期和时间设置", "start ms-settings:dateandtime"),
        ("打开账户信息", "start ms-settings:yourinfo"),
        ("打开个性化设置", "start ms-settings:personalization"),
        ("打开主题设置", "start ms-settings:themes"),
        ("打开锁屏设置", "start ms-settings:lockscreen"),
        ("打开通知设置", "start ms-settings:notifications"),
        ("打开存储设置", "start ms-settings:storagesense"),
        ("打开更新与安全", "start ms-settings:windowsupdate"),
        ("打开备份设置", "start ms-settings:backup"),
        ("打开疑难解答", "start ms-settings:troubleshoot"),
        ("打开激活设置", "start ms-settings:activation"),
        ("打开远程桌面设置", "start ms-settings:remotedesktop"),
        ("打开默认应用", "start ms-settings:defaultapps"),
        ("打开应用执行别名", "start ms-settings:appsforwebsites"),
        ("打开开发者选项", "start ms-settings:developers"),
    ],

    "办公与效率": [
        ("打开写字板", "start write"),
        ("打开字符映射表", "start charmap"),
        ("打开步骤记录器", "start psr"),
        ("打开便笺", "start stikynot"),
        ("打开放大镜", "start magnify"),
        ("打开讲述人", "start narrator"),
        ("打开屏幕键盘", "start osk"),
        ("打开高对比度设置", "start ms-settings:easeofaccess-highcontrast"),
        ("打开语音识别", "start ms-settings:speech"),
        ("打开任务视图", "powershell explorer.exe shell:::{3080F90E-D7AD-11D9-BD98-0000947B0257}"),
    ],

    "运维与高级功能": [
        ("打开组策略结果", "start rsop.msc"),
        ("打开Windows更新日志", "powershell Get-WindowsUpdateLog"),
        ("生成系统健康报告", "powershell Get-ComputerInfo"),
        ("导出已安装程序列表", "powershell Get-WmiObject -Class Win32_Product | Out-File C:\\installed_apps.txt"),
        ("重启Windows资源管理器", "powershell Stop-Process -Name explorer -Force; Start-Process explorer"),
        ("关机", "powershell Stop-Computer"),
        ("重启", "powershell Restart-Computer"),
        ("注销当前用户", "powershell logoff"),
        ("锁定计算机", "powershell rundll32 user32.dll,LockWorkStation"),
        ("休眠", "powershell rundll32 powrprof.dll,SetSuspendState Hibernate"),
        ("睡眠", "powershell rundll32 powrprof.dll,SetSuspendState Standby"),
    ],

    "WSL / 开发工具": [
        ("打开WSL终端", "wsl"),
        ("打开WSL(默认发行版)", "wsl ~"),
        ("列出WSL发行版", "powershell wsl --list --verbose"),
        ("打开Docker Desktop", "start \"Docker Desktop\" \"C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe\""),
        ("打开Git Bash", "start \"\" \"C:\\Program Files\\Git\\git-bash.exe\""),
        ("打开VS Code", "start code"),
        ("打开Notepad++", "start notepad++"),
    ]
}


        # 创建普通功能选项卡
        normal_tab = QWidget()
        normal_layout = QVBoxLayout(normal_tab)
        normal_sub_tab = QTabWidget()
        for group_name, group_buttons in normal_function_groups.items():
            sub_tab = QWidget()
            sub_layout = QVBoxLayout(sub_tab)
            columns = 3
            grid_layout = QGridLayout()
            for index, (button_text, command) in enumerate(group_buttons):
                row = index // columns
                col = index % columns
                self.add_button(grid_layout, button_text, command, self.log_text, row, col)
            sub_layout.addLayout(grid_layout)
            # 添加普通功能手动执行命令的输入框和按钮
            self.add_custom_command(sub_layout, "手动执行命令", self.log_text, sub_layout.count(), 0)
            normal_sub_tab.addTab(sub_tab, group_name)
        normal_layout.addWidget(normal_sub_tab)

        self.tab_widget.addTab(normal_tab, "普通功能")

        # 定义管理员功能分组，直接用命令字符串
        admin_function_groups = {
            "远程与连接": [
                ("启用远程桌面", 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d 0 /f'),
                ("关闭远程桌面", 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d 1 /f'),
                ("启用无密码连接", 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Lsa" /v LimitBlankPasswordUse /t REG_DWORD /d 0 /f'),
                ("关闭无密码连接", 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Lsa" /v LimitBlankPasswordUse /t REG_DWORD /d 1 /f'),
                ("启用远程协助", 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp" /v UserAuthentication /t REG_DWORD /d 1 /f && netsh advfirewall firewall set rule group="Remote Assistance" new enable=yes'),
                ("关闭远程协助", 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp" /v UserAuthentication /t REG_DWORD /d 0 /f && netsh advfirewall firewall set rule group="Remote Assistance" new enable=no')
            ],
            "安全防护": [
                ("启用 Defender", "powershell -Command \"Set-MpPreference -DisableRealtimeMonitoring $false\""),
                ("禁用 Defender", "powershell -Command \"Set-MpPreference -DisableRealtimeMonitoring $true\""),
                ("用于内置管理员帐户的管理员批准模式", 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v FilterAdministratorToken /t REG_DWORD /d 1 /f'),
                ("关闭 Smartscreen 应用筛选器 (旧版)", 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer" /v SmartScreenEnabled /t REG_SZ /d off /f'),
                ("关闭 Smartscreen 应用筛选器 (新版)", 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer" /v SmartScreenEnabled /t REG_SZ /d off /f & reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\MicrosoftEdge\\PhishingFilter" /v EnabledV9 /t REG_DWORD /d 0 /f'),
                ("关闭 UAC", 'powershell -Command "Set-ItemProperty -Path HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System -Name EnableLUA -Value 0"'),
                ("启用 UAC", 'powershell -Command "Set-ItemProperty -Path HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System -Name EnableLUA -Value 1"'),
                ("禁用 Windows 遥测数据收集", 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f'),
                ("启用 Windows 遥测数据收集", 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 3 /f')
            ],
            "系统服务管理": [
                ("启用 SysMain", "sc config SysMain start= auto && net start SysMain"),
                ("禁用 SysMain", "net stop SysMain && sc config SysMain start= disabled"),
                ("启用 Windows 索引", "sc config WSearch start= auto && net start WSearch"),
                ("禁用 Windows 索引", "net stop WSearch && sc config WSearch start= disabled"),
                ("禁用家庭组服务", "net stop HomeGroupListener && net stop HomeGroupProvider && sc config HomeGroupListener start= disabled && sc config HomeGroupProvider start= disabled"),
                ("启用家庭组服务", "sc config HomeGroupListener start= auto && sc config HomeGroupProvider start= auto && net start HomeGroupListener && net start HomeGroupProvider"),
                ("启用自动更新", "net start wuauserv"),
                ("停止自动更新", "net stop wuauserv"),
                ("启用自动时间同步", "sc config w32time start= auto && net start w32time"),
                ("禁用自动时间同步", "net stop w32time && sc config w32time start= disabled")
            ],
            "系统维护清理": [
                ("清空回收站", 'powershell -NoProfile -Command "Get-ChildItem -Path C:\\$Recycle.Bin -Force -Recurse | Remove-Item -Recurse -Force"'),
                ("清理系统临时文件", 'powershell -Command "Get-ChildItem -Path $env:TEMP -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue"'),
                ("清理 WinTemp", 'powershell -Command "Remove-Item -Path C:\\Windows\\Temp\\* -Recurse -Force -ErrorAction SilentlyContinue"'),
                ("磁盘碎片整理C：", "defrag C: /U /V"),
                ("优化磁盘C：", "defrag C: /O"),
                ("清理 Windows 更新缓存", 'powershell -Command "Remove-Item -Path C:\\Windows\\SoftwareDistribution\\Download\\* -Recurse -Force -ErrorAction SilentlyContinue"'),
                ("禁用 Windows 错误报告", 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\Windows Error Reporting" /v Disabled /t REG_DWORD /d 1 /f'),
                ("启用 Windows 错误报告", 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\Windows Error Reporting" /v Disabled /t REG_DWORD /d 0 /f'),
                ("禁用系统还原", 'powershell Get-ComputerRestorePoint | ForEach-Object { Disable-ComputerRestore -Drive $_.Drive }'),
                ("启用系统还原", 'powershell Enable-ComputerRestore -Drive C:\\')
            ],
            "系统进程管理": [
                ("重启资源管理器", "taskkill /im explorer.exe /f && start explorer.exe"),
                ("杀死资源管理器", "taskkill /im explorer.exe /f"),
                ("启动资源管理器", "start explorer.exe"),
                ("杀死命令提示符", "taskkill /im cmd.exe /f"),
            ], 
            "系统启动设置": [
                ("禁用快速启动", "powercfg /h off"),
                ("启用快速启动", "powercfg /h on"),
                ("禁用应用自动启动", 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /f && reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run" /f'),
                ("启用应用自动启动", "echo 需手动配置注册表项恢复自动启动程序"),
                ("禁用休眠功能", "powercfg /hibernate off"),
                ("启用休眠功能", "powercfg /hibernate on")
            ],
            "网络管理配置": [
                ("刷新 DNS", "ipconfig /flushdns"),
                ("释放 IP", "ipconfig /release"),
                ("重新获取 IP", "ipconfig /renew"),
                ("重启 DNS 缓存", "net stop dnscache && net start dnscache"),
                ("禁用网络发现", 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Parameters" /v AutoShareServer /t REG_DWORD /d 0 /f && reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\LanmanWorkstation\\Parameters" /v DisallowUnencryptedGuestAuth /t REG_DWORD /d 1 /f'),
                ("启用网络发现", 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Parameters" /v AutoShareServer /t REG_DWORD /d 1 /f && reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\LanmanWorkstation\\Parameters" /v DisallowUnencryptedGuestAuth /t REG_DWORD /d 0 /f'),
                ("重置 Winsock", "netsh winsock reset")
            ],
            "Windows 更新设置": [
                ("禁用自动更新驱动", 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DriverSearching" /v DontSearchWindowsUpdate /t REG_DWORD /d 1 /f && reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DriverSearching" /v SearchOrderConfig /t REG_DWORD /d 0 /f'),
                ("启用自动更新驱动", 'reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DriverSearching" /v DontSearchWindowsUpdate /f && reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DriverSearching" /v SearchOrderConfig /f')
            ],
            "时间与时区管理": [
                ("同步 Internet 时间", "w32tm /resync"),
                ("查看当前时区", "tzutil /g"),
                ("设为北京时区", 'tzutil /s "China Standard Time"')
            ],
            "视觉效果设置": [
                ("低质量壁纸", 'reg add "HKCU\\Control Panel\\Desktop" /v JPEGImportQuality /t REG_DWORD /d 96 /f'),
                ("默认质量壁纸", 'reg delete "HKCU\\Control Panel\\Desktop" /v JPEGImportQuality /f'),
                ("高质量壁纸", 'reg add "HKCU\\Control Panel\\Desktop" /v JPEGImportQuality /t REG_DWORD /d 256 /f')
            ],
            "安全扫描": [
                ("全盘扫描", 'powershell -Command "Start-MpScan -ScanType FullScan"')
            ],
            "系统还原": [
                ("创建还原点", 'powershell -Command "Checkpoint-Computer -Description \'System Optimizer Restore Point\' -RestorePointType MODIFY_SETTINGS"')
            ]
        }

        # 创建管理员功能选项卡
        admin_tab = QWidget()
        admin_layout = QVBoxLayout(admin_tab)
        admin_sub_tab = QTabWidget()
        for group_name, group_buttons in admin_function_groups.items():
            sub_tab = QWidget()
            sub_layout = QVBoxLayout(sub_tab)
            columns = 3
            grid_layout = QGridLayout()
            for index, (button_text, command) in enumerate(group_buttons):
                row = index // columns
                col = index % columns
                self.add_button(grid_layout, button_text, command, self.log_text, row, col)
            sub_layout.addLayout(grid_layout)
            # 添加管理员功能手动执行命令的输入框和按钮
            self.add_custom_command(sub_layout, "手动执行命令", self.log_text, sub_layout.count(), 0)
            admin_sub_tab.addTab(sub_tab, group_name)
        admin_layout.addWidget(admin_sub_tab)

        self.tab_widget.addTab(admin_tab, "管理员功能")

        # 根据是否具有管理员权限，启用或禁用管理员功能选项卡
        admin_tab.setEnabled(is_admin())

        # 检查是否具有管理员权限，并在日志文本框中输出相应信息
        if not is_admin():
            self.log_text.append('<span style="color: orange;">未检测到管理员权限，部分功能将不可用。</span>')
            print("未检测到管理员权限，部分功能将不可用。")
            self.log_text.append("Windows PowerShell\n版权所有 (C) Microsoft Corporation。保留所有权利。\n\n尝试新的跨平台 PowerShell https://aka.ms/pscore6")
        else:
            self.log_text.append('<span style="color: green;">已检测到管理员权限，所有功能均可使用。</span>')
            print("已检测到管理员权限，所有功能均可使用。")
            self.log_text.append("Windows PowerShell\n版权所有 (C) Microsoft Corporation。保留所有权利。\n\n尝试新的跨平台 PowerShell https://aka.ms/pscore6")

        # 创建系统信息选项卡
        system_info_tab = QWidget()
        system_info_layout = QVBoxLayout(system_info_tab)

        # CPU 信息
        self.cpu_label = QLabel(f"CPU 使用率: {psutil.cpu_percent()}%")
        system_info_layout.addWidget(self.cpu_label)

        # 内存信息
        memory = psutil.virtual_memory()
        self.memory_label = QLabel(f"内存使用率: {memory.percent}%")
        system_info_layout.addWidget(self.memory_label)

        # 磁盘信息
        disk = psutil.disk_usage('/')
        self.disk_label = QLabel(f"磁盘使用率: {disk.percent}%")
        system_info_layout.addWidget(self.disk_label)

        # 网络信息
        net_io = psutil.net_io_counters()
        self.net_label = QLabel(f"网络上传: {net_io.bytes_sent} 字节, 下载: {net_io.bytes_recv} 字节")
        system_info_layout.addWidget(self.net_label)

        self.tab_widget.addTab(system_info_tab, "系统信息")

        # 创建定时器，每 2 秒刷新一次系统信息
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_system_info)
        self.timer.start(2000)

    def update_system_info(self):
        # 更新 CPU 信息
        cpu_percent = psutil.cpu_percent()
        self.cpu_label.setText(f"CPU 使用率: {cpu_percent}%")

        # 更新内存信息
        memory = psutil.virtual_memory()
        self.memory_label.setText(f"内存使用率: {memory.percent}%")

        # 更新磁盘信息
        disk = psutil.disk_usage('/')
        self.disk_label.setText(f"磁盘使用率: {disk.percent}%")

        # 更新网络信息
        net_io = psutil.net_io_counters()
        self.net_label.setText(f"网络上传: {net_io.bytes_sent} 字节, 下载: {net_io.bytes_recv} 字节")

    def add_button(self, outer_layout, button_text, command, log_widget, row, col):
        button = QPushButton()
        # 优化按钮样式，移除不支持的属性
        button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setMinimumSize(200, 48)

        # 使用 QLabel 实现文字换行
        label = QLabel(button_text)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignCenter)

        # 按钮内部的布局
        button_layout = QVBoxLayout(button)
        button_layout.addWidget(label)
        button_layout.setContentsMargins(0, 0, 0, 0)

        button.clicked.connect(lambda: self.execute_command(command, log_widget))
        # 使用外部传入的布局添加按钮
        outer_layout.addWidget(button, row, col)

    def add_custom_command(self, layout, label_text, log_widget, row, col):
        if isinstance(layout, QGridLayout):
            label = QLabel(label_text)
            # 增大标签字体大小
            label.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    font-weight: 500;
                    margin-bottom: 8px;
                }
            """)
            layout.addWidget(label, row, col, 1, 3)  # 跨 3 列
            row += 1
            command_input = QLineEdit()
            # 优化输入框样式
            command_input.setStyleSheet("""
                QLineEdit {
                    background-color: white;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 14px;
                }
                QLineEdit:focus {
                    border-color: #2196F3;
                }
            """)
            layout.addWidget(command_input, row, col, 1, 3)  # 跨 3 列
            row += 1
            button = QPushButton("执行命令")
            # 设置按钮样式表，修改字体大小为 14px 避免文字溢出，移除不支持的属性
            button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    padding: 12px 24px;
                    border: none;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3e8e41;
                }
            """)
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            button.setMinimumSize(200, 48)
            button.clicked.connect(lambda: self.execute_custom_command(command_input.text(), log_widget))
            layout.addWidget(button, row, col, 1, 3, alignment=Qt.AlignCenter)  # 跨 3 列并居中
        else:
            label = QLabel(label_text)
            label.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    font-weight: 500;
                    margin-bottom: 8px;
                }
            """)
            layout.addWidget(label)
            command_input = QLineEdit()
            command_input.setStyleSheet("""
                QLineEdit {
                    background-color: white;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 14px;
                }
                QLineEdit:focus {
                    border-color: #2196F3;
                }
            """)
            layout.addWidget(command_input)
            button = QPushButton("执行命令")
            button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    padding: 12px 24px;
                    border: none;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3e8e41;
                }
            """)
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            button.setMinimumSize(200, 48)
            button.clicked.connect(lambda: self.execute_custom_command(command_input.text(), log_widget))
            layout.addWidget(button, alignment=Qt.AlignCenter)

    def execute_command(self, command, log_widget):
        if confirm_action(self, f"你确定要执行命令: “{command}” 吗？"):
            run_command(command, log_widget)

    def execute_custom_command(self, command, log_widget):
        if confirm_action(self, f"你确定要执行命令: “{command}” 吗？"):
            run_command(command, log_widget)


# 检测系统主题
def get_system_theme():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return "light" if value == 1 else "dark"
    except Exception:
        return "light"

# -------------------------------------------------
# 启动入口（放到文件最底部，顶格写）
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SystemOptimizer()
    window.show()
    print("系统优化工具已启动")
    print("EndlessPixel by system_mini")
    print("版本信息：")
    print("b1.0")
    print("感谢您的使用！")
    sys.exit(app.exec_())
