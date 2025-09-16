import os, uuid, json, winreg, random, string
from pathlib import Path

def get_storage_file_path():
    appdata = os.environ.get('APPDATA')
    if appdata:
        return Path(appdata) / "Cursor" / "User" / "globalStorage" / "storage.json"
    return None

def generate_random_hex(length):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))

def new_standard_machine_id():
    uid = uuid.uuid4()
    return str(uid)

def update_machine_guid():
    print("[INFO] 更新注册表中的MachineGuid...")
    reg_path = r"SOFTWARE\Microsoft\Cryptography"
    reg_key_name = "MachineGuid"

    try:
        hklm = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        crypto_key = winreg.OpenKey(hklm, reg_path, 0, winreg.KEY_READ | winreg.KEY_WRITE)
        
        new_guid = str(uuid.uuid4())
        winreg.SetValueEx(crypto_key, reg_key_name, 0, winreg.REG_SZ, new_guid)
        
        verify_guid = winreg.QueryValueEx(crypto_key, reg_key_name)[0]
        if verify_guid == new_guid:
            print(f"[INFO] 注册表更新已成功验证")
            return True
        else:
            print(f"[ERROR] 注册表验证失败: 更新值 ({verify_guid}) 与预期值 ({new_guid}) 不匹配")
            return False
    except Exception as e:
        print(f"[ERROR] 设置注册表值 {reg_key_name} 失败: {e}")
        return False

def update_storage_file(storage_file_path, machine_id, mac_machine_id, dev_device_id, sqm_id):
    if not os.path.exists(storage_file_path):
        print(f"[ERROR] 配置文件未找到: {storage_file_path}")
        print("[TIP] 请先安装并运行一次编辑器，然后再使用")
        return False
    
    try:
        with open(storage_file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if 'telemetry' not in config:
            config['telemetry'] = {}
        config['telemetry']['machineId'] = machine_id
        config['telemetry']['macMachineId'] = mac_machine_id
        config['telemetry']['devDeviceId'] = dev_device_id
        config['telemetry']['sqmId'] = sqm_id
        updated_json = json.dumps(config, indent=2)
        with open(storage_file_path, 'w', encoding='utf-8') as f:
            f.write(updated_json)
        
        print(f"[INFO] 配置文件已成功更新: {storage_file_path}")
        return True
    
    except Exception as e:
        print(f"[ERROR] 更新配置文件失败: {e}")
        return False

def reset_cursor():
    storage_file_path = get_storage_file_path()
    if not storage_file_path:
        print("[ERROR] 无法确定存储文件路径")
        return False
    
    print("[INFO] 生成新的ID...")
    mac_machine_id = new_standard_machine_id()
    uuid_str = str(uuid.uuid4())
    prefix_hex = "".join([format(b, '02x') for b in b'auth0|user_'])
    random_part = generate_random_hex(32)
    machine_id = f"{prefix_hex}{random_part}"
    sqm_id = f"{{{str(uuid.uuid4()).upper()}}}"
    
    update_machine_guid()
    
    print("[INFO] 更新配置...")
    storage_update_successful = update_storage_file(
        storage_file_path,
        machine_id,
        mac_machine_id,
        uuid_str,
        sqm_id
    )
    
    if storage_update_successful:
        print("[INFO] 配置更新成功")
        print("[INFO] 配置更新详情:")
        print(f"[DEBUG] machineId: {machine_id}")
        print(f"[DEBUG] macMachineId: {mac_machine_id}")
        print(f"[DEBUG] devDeviceId: {uuid_str}")
        print(f"[DEBUG] sqmId: {sqm_id}")
        return True
    else:
        print("[ERROR] 更新配置文件失败")
        return False

if __name__ == "__main__":
    while True:
        choice = input("是否确定要执行操作？(y/n): ").strip().lower()
        if choice in ['y', 'yes', '是']:
            print("\n开始执行操作...")
            reset_cursor()
            break
        elif choice in ['n', 'no', '否']:
            print("\n操作已取消。")
            break
        else:
            print("请输入 y/yes/是 确认执行，或 n/no/否 取消操作")  
    input("\n按Enter键退出...")