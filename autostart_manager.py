"""
开机自启管理模块
通过Windows注册表实现开机自启
"""
import winreg
import sys
import os

REGISTRY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "FileCleaner"

def get_app_path():
    """获取当前程序路径"""
    if getattr(sys, 'frozen', False):
        # 打包后的exe路径
        return sys.executable
    else:
        # 脚本路径
        return os.path.abspath(sys.argv[0])

def enable_autostart():
    """启用开机自启"""
    try:
        app_path = get_app_path()
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_PATH,
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{app_path}"')
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"启用开机自启失败: {e}")
        return False

def disable_autostart():
    """禁用开机自启"""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_PATH,
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        # 值不存在，视为成功
        return True
    except Exception as e:
        print(f"禁用开机自启失败: {e}")
        return False

def is_autostart_enabled():
    """检查是否已启用开机自启"""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_PATH,
            0,
            winreg.KEY_READ
        )
        value, _ = winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        
        # 检查路径是否匹配
        return value == f'"{get_app_path()}"'
    except FileNotFoundError:
        return False
    except Exception:
        return False
