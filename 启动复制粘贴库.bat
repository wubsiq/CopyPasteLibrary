@echo off
REM 启动复制粘贴库

REM 检测并终止旧的pythonw.exe进程
 taskkill /IM pythonw.exe /F >nul 2>&1

REM 启动新的服务
 start pythonw main.py

REM 显示启动信息
echo CopyPasteLibrary 已启动
echo 按下 Ctrl+空格 来显示/隐藏窗口

REM 延迟2秒后自动退出
 timeout /t 2 >nul
 exit
