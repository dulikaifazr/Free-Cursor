import tkinter as tk
import os
import sys
import ctypes
import base64
import datetime
import json
import hashlib
import ntplib
from app_ui import FreeCursorApp

class UsageLimiter:
    MAX_DAILY_RESETS = (#阿拉伯数字，自己随便定义)
    TIME_DIFF_THRESHOLD = (#阿拉伯数字，自己随便定义)
    NTP_SERVERS = [
       #自己去寻找ntp的网址，如果觉得自己使用完全不需要，就删除这段代码
    ]
    def __init__(self):
        self.config_paths = self._get_config_paths()
        self.usage_data = self._load_usage_data()
        self._update_usage_data()
    
    def _encrypt_data(self, data):
        username = os.getenv('USERNAME', '')
        computername = os.getenv('COMPUTERNAME', '')
        key = hashlib.md5((f"FreeCursor{username}{computername}").encode()).hexdigest()
        
        data_copy = data.copy()
        data_string = json.dumps(data, sort_keys=True)
        data_copy["verify"] = hashlib.sha256((data_string + key).encode()).hexdigest()
        
        json_data = json.dumps(data_copy)
        encrypted = base64.b64encode(json_data.encode()).decode()
        
        return encrypted
    
    def _decrypt_data(self, encrypted):
        try:
            username = os.getenv('USERNAME', '')
            computername = os.getenv('COMPUTERNAME', '')
            key = hashlib.md5((f"FreeCursor{username}{computername}").encode()).hexdigest()
            
            json_data = base64.b64decode(encrypted.encode()).decode()
            data = json.loads(json_data)
            
            verify = data.pop("verify", "")
            data_string = json.dumps(data, sort_keys=True)
            expected = hashlib.sha256((data_string + key).encode()).hexdigest()
            
            if verify != expected:
                raise ValueError("数据验证失败")
                
            return data
        except Exception as e:
            print(f"解密失败: {e}")
            return None
    
    def _save_usage_data(self):
        encrypted = self._encrypt_data(self.usage_data)
        
        success_count = 0
        for path in self.config_paths:
            try:
                directory = os.path.dirname(path)
                if not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
                    
                with open(path, 'w') as f:
                    f.write(encrypted)
                success_count += 1
            except Exception as e:
                print(f"保存到 {path} 失败: {e}")
                continue
        
        if success_count == 0:
            try:
                main_path = self.config_paths[0]
                directory = os.path.dirname(main_path)
                os.makedirs(directory, exist_ok=True)
                
                with open(main_path, 'w') as f:
                    f.write(encrypted)
            except Exception as e:
                print(f"保存主文件失败: {e}")
    
    def _load_usage_data(self):
        results = []
        file_exists = False
        
        for path in self.config_paths:
            if os.path.exists(path):
                file_exists = True
                try:
                    with open(path, 'r') as f:
                        encrypted = f.read()
                        data = self._decrypt_data(encrypted)
                        if data:
                            results.append(data)
                except Exception as e:
                    print(f"从 {path} 加载失败: {e}")
                    continue
        
        if file_exists and not results:
            ntp_time = self._get_network_time()
            today = ntp_time.strftime("%Y-%m-%d")
            return {
                "last_used_date": today,
                "daily_count": self.MAX_DAILY_RESETS
            }
        
        if not results:
            return {
                "last_used_date": "",
                "daily_count": 0
            }
        
        if len(results) > 1 and len(set(json.dumps(r, sort_keys=True) for r in results)) > 1:
            ntp_time = self._get_network_time()
            today = ntp_time.strftime("%Y-%m-%d")
            
            return {
                "last_used_date": today,
                "daily_count": self.MAX_DAILY_RESETS
            }
            
        return results[0]
    
    def _get_network_time(self):
        ntp_client = ntplib.NTPClient()
        
        for server in self.NTP_SERVERS:
            try:
                response = ntp_client.request(server, timeout=5)
                ntp_time = datetime.datetime.fromtimestamp(response.tx_time)
                
                system_time = datetime.datetime.now()
                time_diff = abs((system_time - ntp_time).total_seconds())
                
                if time_diff > self.TIME_DIFF_THRESHOLD:
                    print(f"检测到时间差异! 系统时间: {system_time}, NTP时间: {ntp_time}, 差异: {time_diff}秒")
                
                return ntp_time
            except Exception as e:
                print(f"NTP服务器 {server} 连接失败: {e}")
                continue
        
        print("警告: 无法获取网络时间，回退到系统时间")
        return datetime.datetime.now()
    
    def _update_usage_data(self):
        ntp_time = self._get_network_time()
        today = ntp_time.strftime("%Y-%m-%d")
        
        if self.usage_data["last_used_date"] != today:
            self.usage_data["last_used_date"] = today
            self.usage_data["daily_count"] = 0
            self._save_usage_data()
    
    def can_use(self):
        return self.usage_data["daily_count"] < self.MAX_DAILY_RESETS
    
    def register_usage(self):
        if self.can_use():
            self.usage_data["daily_count"] += 1
            self._save_usage_data()
            return True
        return False
    
    def get_remaining_uses(self):
        return max(0, self.MAX_DAILY_RESETS - self.usage_data["daily_count"])
    
    def get_time_difference(self):
        try:
            system_time = datetime.datetime.now()
            ntp_time = self._get_network_time()
            return abs((system_time - ntp_time).total_seconds())
        except:
            return 0

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        return True
    return False

def main():
    if run_as_admin():
        sys.exit(0)
        
    root = tk.Tk()
    usage_limiter = UsageLimiter()
    app = FreeCursorApp(root, usage_limiter)
    
    def on_closing():
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main() 
