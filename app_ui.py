import tkinter as tk
from tkinter import messagebox
import os
import sys
import threading
import datetime
import json
import io
import base64
import webbrowser
import requests
from PIL import Image, ImageTk

try:
    from app_resources import ICON_B64
except ImportError:
    ICON_B64 = ""#(app.resources.py的图标自己可以随意找，如果不需要图标测可以删除这个文件中关于icon_b64图标的全部引用)

class FreeCursorApp:
    VERSION = "版本信息"
    VERSION_URL = "你的gist地址"
    GITHUB_REPO_URL = "有了新版本、出现网络连接错误后希望跳转的地址，如果不需要可以删除这段版本可控制代码"
    def __init__(self, root, usage_limiter):
        self.root = root
        self.root.title("Free-Cursor")
        
        self.usage_limiter = usage_limiter
        
        window_width = 360
        window_height = 400
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.resizable(False, False)
        
        if self.check_for_updates_blocking():
            self.root.after(1000, self.root.destroy)
            return
        
        try:
            if ICON_B64:
                icon_data = base64.b64decode(ICON_B64)
                icon_file = "temp_icon.ico"
                with open(icon_file, "wb") as f:
                    f.write(icon_data)
                self.root.iconbitmap(icon_file)
                os.remove(icon_file)
            else:
                self.root.iconbitmap("icon.ico")
        except Exception as e:
            print(f"加载图标失败: {e}")
        
        self.setup_ui()
        self.check_time_tampering()
        self.schedule_update_check()
    
    def check_for_updates_blocking(self):
        random_param = f"?t={datetime.datetime.now().timestamp()}"
        version_url = f"{self.VERSION_URL}{random_param}"
        
        version_info = None
        try:
            response = requests.get(version_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    version_info = data[0]
                else:
                    version_info = data
        except Exception as e:
            print(f"获取版本信息时出错: {e}")
        
        if version_info is None:
            messagebox.showerror(
                "无法验证版本", 
                f"无法连接到服务器验证版本信息。请检查您的网络连接，或访问我们的GitHub页面获取最新版本。\n\n按确定将打开GitHub页面。"
            )
            webbrowser.open(self.GITHUB_REPO_URL)
            return True
        
        latest_version = version_info.get("latest_version")
        download_url = version_info.get("download_url", self.GITHUB_REPO_URL)
        min_allowed_version = version_info.get("min_allowed_version")
        
        if latest_version and self.is_newer_version(latest_version):
            messagebox.showerror(
                "发现新版本", 
                f"当前版本 {self.VERSION} 已过期，最新版本为 {latest_version}。\n请更新到最新版本以继续使用。\n\n按确定将打开下载页面。"
            )
            webbrowser.open(download_url)
            return True
        
        if min_allowed_version and self.is_version_lower_than(self.VERSION, min_allowed_version):
            messagebox.showerror(
                "版本不支持", 
                f"当前版本 {self.VERSION} 已不再受支持，最低要求版本为 {min_allowed_version}。\n\n按确定将打开下载页面。"
            )
            webbrowser.open(download_url)
            return True
        
        return False
    
    def is_newer_version(self, latest_version):
        current = [int(x) for x in self.VERSION.split(".")]
        latest = [int(x) for x in latest_version.split(".")]
        
        for i in range(max(len(current), len(latest))):
            c = current[i] if i < len(current) else 0
            l = latest[i] if i < len(latest) else 0
            if l > c:
                return True
            elif l < c:
                return False
        return False
    
    def is_version_lower_than(self, current_version, min_allowed_version):
        current = [int(x) for x in current_version.split(".")]
        min_allowed = [int(x) for x in min_allowed_version.split(".")]
        
        for i in range(max(len(current), len(min_allowed))):
            c = current[i] if i < len(current) else 0
            m = min_allowed[i] if i < len(min_allowed) else 0
            if m > c:
                return True
            elif m < c:
                return False
        return False
    
    def setup_ui(self):
        self.root.configure(bg="white")
        
        main_frame = tk.Frame(self.root, bg="white")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        try:
            if ICON_B64:
                icon_data = base64.b64decode(ICON_B64)
                icon_image = Image.open(io.BytesIO(icon_data))
            else:
                icon_image = Image.open("icon.ico")
            
            icon_image = icon_image.resize((120, 120), Image.LANCZOS)
            self.icon_photo = ImageTk.PhotoImage(icon_image)
            
            icon_label = tk.Label(main_frame, image=self.icon_photo, bg="white")
            icon_label.pack(pady=(10, 5))
        except Exception as e:
            print(f"无法加载图标作为图像: {e}")
            
            canvas = tk.Canvas(main_frame, width=120, height=120, bg="white", highlightthickness=0)
            canvas.pack(pady=(10, 5))
            
            canvas.create_oval(10, 10, 110, 110, fill="#1E90FF", outline="#1E88E5", width=2)
            canvas.create_oval(45, 30, 55, 40, fill="white", outline="")
        
        self.title_label = tk.Label(
            main_frame, 
            text="Free-Cursor", 
            font=("Microsoft YaHei UI", 20, "bold"),
            bg="white", 
            fg="#2E86C1",
            bd=0
        )
        self.title_label.pack(pady=(10, 15))
        
        button_frame = tk.Frame(main_frame, bg="white")
        button_frame.pack(pady=5)
        
        self.btn_reset = tk.Button(
            button_frame, 
            text="打造干净环境", 
            bg="#4A69BD",
            fg="white", 
            font=("Microsoft YaHei UI", 12),
            width=22,
            height=2,
            relief=tk.FLAT,
            bd=0,
            activebackground="#3C579A",
            activeforeground="white",
            cursor="hand2",
            command=self.reset_cursor_pro
        )
        self.btn_reset.pack(pady=(0, 8))
        
        def open_proton_mail():
            webbrowser.open("https://account.proton.me/mail")
            
        self.btn_mail = tk.Button(
            button_frame, 
            text="自己注册稳定邮箱", 
            bg="#4A69BD",
            fg="white", 
            font=("Microsoft YaHei UI", 11),
            width=22,
            height=1,
            relief=tk.FLAT,
            bd=0,
            activebackground="#219653",
            activeforeground="white",
            cursor="hand2",
            command=open_proton_mail
        )
        self.btn_mail.pack(pady=(0, 8))
        
        description_frame = tk.Frame(main_frame, bg="white")
        description_frame.pack(pady=(5, 0))
        
        description = "点击按钮"
        desc_label = tk.Label(
            description_frame, 
            text=description, 
            font=("Microsoft YaHei UI", 10),
            bg="white", 
            fg="#555555",
            bd=0
        )
        desc_label.pack()
        
        max_resets = getattr(self.usage_limiter, 'MAX_DAILY_RESETS', 2)
        self.usage_label = tk.Label(
            main_frame,
            text=f"今日剩余使用次数: {self.usage_limiter.get_remaining_uses()}/{max_resets}",
            font=("Microsoft YaHei UI", 10),
            bg="white",
            fg="#555555"
        )
        self.usage_label.pack(pady=(5, 10))
        
        footer_frame = tk.Frame(main_frame, bg="white")
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.version_label = tk.Label(
            footer_frame, 
            text=f"版本: {self.VERSION}", 
            font=("Microsoft YaHei UI", 9),
            bg="white", 
            fg="#888888",
            bd=0
        )
        self.version_label.pack(side=tk.RIGHT, pady=5)
        
        copyright_label = tk.Label(
            footer_frame, 
            text="© 2025", 
            font=("Microsoft YaHei UI", 9),
            bg="white", 
            fg="#888888",
            bd=0
        )
        copyright_label.pack(side=tk.LEFT, pady=5)
        
        self.update_button_state()
    
    def update_button_state(self):
        time_diff = self.usage_limiter.get_time_difference()
        
        if time_diff > self.usage_limiter.TIME_DIFF_THRESHOLD:
            self.btn_reset.config(
                state=tk.DISABLED,
                text="系统时间异常 - 请校准时间",
                bg="#FF4500"
            )
        elif not self.usage_limiter.can_use():
            self.btn_reset.config(
                state=tk.DISABLED,
                text="今日使用次数已达上限",
                bg="#8F8F8F"
            )
    
    def reset_cursor_pro(self):
        if self.check_for_updates_blocking():
            return
        
        time_diff = self.usage_limiter.get_time_difference()
        if time_diff > self.usage_limiter.TIME_DIFF_THRESHOLD:
            messagebox.showerror("系统时间异常", "检测到系统时间异常！请将系统时间调整为正确的时间后再使用本程序。")
            return
            
        if not self.usage_limiter.can_use():
            max_resets = getattr(self.usage_limiter, 'MAX_DAILY_RESETS', 2)
            messagebox.showinfo("使用限制", f"今日使用次数已达上限({max_resets}次)，请明天再试。")
            return
        
        self.btn_reset.config(state=tk.DISABLED, text="正在打造纯净环境中...", bg="#8F8F8F")
        self.root.update()
        
        def run_reset():
            try:
                success = True
                self.root.after(0, lambda: self.reset_completed(success))
            except Exception as e:
                self.root.after(0, lambda: self.show_error(str(e)))
        
        reset_thread = threading.Thread(target=run_reset)
        reset_thread.daemon = True
        reset_thread.start()
    
    def reset_completed(self, success):
        if success:
            self.usage_limiter.register_usage()
            max_resets = getattr(self.usage_limiter, 'MAX_DAILY_RESETS', 2)
            self.usage_label.config(text=f"今日剩余使用次数: {self.usage_limiter.get_remaining_uses()}/{max_resets}")
            
            messagebox.showinfo("成功", "打造干净环境成功")
        else:
            messagebox.showerror("错误", "打造干净环境未成功")
        
        if self.usage_limiter.can_use():
            self.btn_reset.config(state=tk.NORMAL, text="打造干净环境", bg="#4A69BD")
        else:
            self.btn_reset.config(state=tk.DISABLED, text="今日使用次数已达上限", bg="#8F8F8F")
    
    def show_error(self, error_msg):
        messagebox.showerror("错误", f"发生错误: {error_msg}")
        self.btn_reset.config(state=tk.NORMAL, text="打造干净环境未成功", bg="#4A69BD")
    
    def schedule_update_check(self):
        check_interval = 1800000
        
        def periodic_check():
            threading.Thread(target=self.background_update_check, daemon=True).start()
            self.root.after(check_interval, periodic_check)
            
        self.root.after(check_interval, periodic_check)
        
    def background_update_check(self):
        try:
            if self.check_for_updates_blocking():
                self.root.after(0, lambda: messagebox.showerror("版本已过期", "检测到新版本，程序将关闭。请下载最新版本。"))
                self.root.after(1000, self.root.destroy)
        except Exception as e:
            print(f"后台版本检查失败: {e}")

    def check_time_tampering(self):
        time_diff = self.usage_limiter.get_time_difference()
        
        if time_diff > self.usage_limiter.TIME_DIFF_THRESHOLD:
            penalty_message = "检测到系统时间异常！\n\n请将系统时间调整为正确的时间后再使用本程序。"
            messagebox.showerror("系统时间异常", penalty_message)
            self.update_button_state() 
