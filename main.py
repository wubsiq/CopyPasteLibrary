import tkinter as tk
import keyboard
import threading
import pyperclip
import time
import json
import os
from pynput.keyboard import Controller, Key
import pystray
from PIL import Image, ImageDraw

class CopyPasteLibrary:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CopyPasteLibrary")
        
        # 加载保存的窗口大小
        self.load_window_size()
        
        self.root.withdraw()  # 初始隐藏窗口
        self.root.attributes('-topmost', True)  # 窗口置顶
        
        # 用于标记是否是程序自身的复制操作
        self.is_self_copy = False
        
        # 监听窗口大小变化
        self.root.bind('<Configure>', self.on_configure)
        
        # 设置暗灰色背景和黑色线条
        self.root.config(bg="#2d2d2d")
        
        # 创建框架容纳内容
        self.main_frame = tk.Frame(self.root, bg="#2d2d2d")
        self.main_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # 创建滚动条
        self.scrollbar = tk.Scrollbar(self.main_frame, orient=tk.VERTICAL, bg="#3d3d3d", troughcolor="#2d2d2d")
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建画布
        self.canvas = tk.Canvas(self.main_frame, bg="#2d2d2d", yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.canvas.yview)
        
        # 创建内部框架
        self.content_frame = tk.Frame(self.canvas, bg="#2d2d2d")
        self.canvas.create_window((0, 0), window=self.content_frame, anchor=tk.NW)
        
        # 绑定双击事件到画布
        self.content_frame.bind('<Double-1>', self.on_double_click)
        
        # 绑定鼠标滚轮事件
        self.canvas.bind_all('<MouseWheel>', self.on_mousewheel)
        
        # 添加清空按钮
        self.clear_button = tk.Button(
            self.root, 
            text="清空历史", 
            command=self.clear_history,
            bg="#4d4d4d", 
            fg="#ffffff", 
            relief=tk.SOLID, 
            borderwidth=1,
            highlightbackground="#000000"
        )
        self.clear_button.pack(pady=5, padx=10, anchor=tk.CENTER)
        
        # 历史记录
        self.history = []
        self.last_clipboard = ""
        
        # 键盘控制器
        self.keyboard = Controller()
        
        # 加载历史记录
        self.load_history()
        
        # 启动剪贴板监听器
        self.clipboard_monitor = ClipboardMonitor(self)
        self.clipboard_monitor.start()
        
        # 监听快捷键
        self.setup_hotkey()
        
        # 创建系统托盘图标
        self.create_tray_icon()
        
    def setup_hotkey(self):
        def on_hotkey():
            if self.root.state() == 'withdrawn':
                # 显示窗口并定位到鼠标位置
                x = self.root.winfo_pointerx()
                y = self.root.winfo_pointery()
                self.root.geometry(f"400x300+{x}+{y}")
                self.root.deiconify()
                self.root.lift()
            else:
                # 隐藏窗口
                self.root.withdraw()
        
        keyboard.add_hotkey('ctrl+space', on_hotkey)
    
    def on_double_click(self, event, index=None):
        # 双击执行粘贴
        if index is not None and 0 <= index < len(self.history):
            item = self.history[index]
            self.smart_paste(item['content'])
    
    def smart_paste(self, content):
        # 智能粘贴逻辑
        # 保存当前剪贴板内容
        current_clipboard = pyperclip.paste()
        
        # 将选中内容写入剪贴板
        pyperclip.copy(content)
        
        # 模拟Ctrl+V
        self.keyboard.press(Key.ctrl)
        self.keyboard.press('v')
        self.keyboard.release('v')
        self.keyboard.release(Key.ctrl)
        
        # 恢复之前的剪贴板内容
        pyperclip.copy(current_clipboard)
    
    def add_to_history(self, content):
        # 去重检查
        if content == self.last_clipboard:
            return
        
        # 创建新记录
        new_item = {
            'id': len(self.history) + 1,
            'content': content,
            'time': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 添加到历史记录
        self.history.insert(0, new_item)
        self.last_clipboard = content
        
        # 限制历史记录数量
        if len(self.history) > 100:
            self.history = self.history[:100]
        
        # 更新Listbox
        self.update_listbox()
        
        # 保存历史记录
        self.save_history()
    
    def update_listbox(self):
        # 清空内容框架
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # 添加历史记录到内容框架
        for index, item in enumerate(self.history):
            # 只显示前30个字符，去掉不需要的字段
            content = item['content']
            # 检查是否包含不需要的字段
            if '📋 项目名称：CopyPasteLibrary (复制粘贴库' in content:
                continue
            preview = content[:30] + ('...' if len(content) > 30 else '')
            
            # 创建记录框架
            record_frame = tk.Frame(self.content_frame, bg="#3d3d3d", borderwidth=1, relief=tk.SOLID, highlightbackground="#000000")
            record_frame.pack(fill=tk.X, pady=2, padx=2)
            record_frame.bind('<Double-1>', lambda e, idx=index: self.on_double_click(e, idx))
            
            # 添加文本标签
            text_label = tk.Label(record_frame, text=preview, bg="#3d3d3d", fg="#ffffff", anchor=tk.W, padx=5, pady=3)
            text_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # 添加复制按钮
            copy_button = tk.Button(
                record_frame, 
                text="复制", 
                command=lambda idx=index: self.copy_item(idx),
                bg="#4d4d4d", 
                fg="#ffffff", 
                relief=tk.SOLID, 
                borderwidth=1,
                highlightbackground="#000000"
            )
            copy_button.pack(side=tk.RIGHT, padx=5, pady=3)
        
        # 更新画布滚动区域
        self.content_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox('all'))
    
    def copy_item(self, index):
        # 复制选中的内容
        if 0 <= index < len(self.history):
            item = self.history[index]
            # 标记为程序自身的复制操作
            self.is_self_copy = True
            pyperclip.copy(item['content'])
            # 短暂延迟后重置标记
            import threading
            threading.Timer(0.1, lambda: setattr(self, 'is_self_copy', False)).start()
    
    def on_mousewheel(self, event):
        # 处理鼠标滚轮事件
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def clear_history(self):
        # 清空历史记录
        self.history = []
        self.last_clipboard = ""
        self.update_listbox()
        self.save_history()
    
    def load_window_size(self):
        # 加载保存的窗口大小
        config_file = 'config.json'
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    if 'window_size' in config:
                        width, height = config['window_size']
                        self.root.geometry(f"{width}x{height}")
                        return
            except Exception as e:
                print(f"加载窗口大小失败: {e}")
        # 默认窗口大小
        self.root.geometry("500x400")
    
    def save_window_size(self):
        # 保存当前窗口大小
        config_file = 'config.json'
        try:
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            config = {'window_size': [width, height]}
            with open(config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"保存窗口大小失败: {e}")
    
    def on_configure(self, event):
        # 监听窗口大小变化
        if event.widget == self.root:
            # 只有当窗口可见且大小大于最小值时才保存
            if self.root.state() != 'withdrawn' and event.width > 100 and event.height > 100:
                self.save_window_size()
    
    def create_tray_icon(self):
        # 创建系统托盘图标
        def create_image():
            # 创建一个简单的图标
            image = Image.new('RGB', (64, 64), color='#2d2d2d')
            draw = ImageDraw.Draw(image)
            draw.rectangle([16, 16, 48, 48], fill='#ffffff')
            draw.text([20, 24], 'CP', fill='#2d2d2d', font_size=20)
            return image
        
        def on_quit(icon, item):
            # 退出程序
            icon.stop()
            self.root.quit()
        
        def on_show(icon, item):
            # 显示窗口
            x = self.root.winfo_pointerx()
            y = self.root.winfo_pointery()
            self.root.geometry(f"450x300+{x}+{y}")
            self.root.deiconify()
            self.root.lift()
        
        def on_clear(icon, item):
            # 清空历史记录
            self.clear_history()
        
        # 创建系统托盘图标
        self.tray_icon = pystray.Icon(
            "CopyPasteLibrary",
            create_image(),
            "CopyPasteLibrary",
            menu=pystray.Menu(
                pystray.MenuItem("显示", on_show),
                pystray.MenuItem("清空历史", on_clear),
                pystray.MenuItem("退出", on_quit)
            )
        )
        
        # 启动系统托盘图标
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def save_history(self):
        # 保存历史记录到JSON文件
        with open('history.json', 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
    
    def load_history(self):
        # 从JSON文件加载历史记录
        if os.path.exists('history.json'):
            try:
                with open('history.json', 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
                
                # 更新Listbox
                self.update_listbox()
                
                # 更新最后剪贴板内容
                if self.history:
                    self.last_clipboard = self.history[0]['content']
            except Exception as e:
                print(f"加载历史记录失败: {e}")
    
    def run(self):
        # 运行主循环
        # 重写窗口关闭行为，使其只是隐藏而不是退出
        self.root.protocol("WM_DELETE_WINDOW", self.root.withdraw)
        self.root.mainloop()

class ClipboardMonitor(threading.Thread):
    def __init__(self, app):
        super().__init__(daemon=True)
        self.app = app
    
    def run(self):
        while True:
            try:
                # 检查剪贴板内容
                current_clipboard = pyperclip.paste()
                if current_clipboard and not self.app.is_self_copy:
                    self.app.add_to_history(current_clipboard)
            except Exception as e:
                print(f"剪贴板监听错误: {e}")
            
            # 每0.5秒检查一次
            time.sleep(0.5)

if __name__ == "__main__":
    print("Starting CopyPasteLibrary...")
    print("Press Ctrl+Space to toggle the window")
    try:
        app = CopyPasteLibrary()
        app.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
