"""
配置管理模块
负责读写 config.ini 配置文件
配置文件位置：打包后跟随 exe 目录，开发模式跟随脚本目录
"""
import configparser
import os
import sys
import logging
from pathlib import Path

logger = logging.getLogger('FileCleaner')

def _get_base_dir():
    """获取程序根目录：打包后为 exe 所在目录，开发模式为脚本目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

# 默认配置值
DEFAULT_CONFIG = {
    'directory_path': r'C:\zl_robot\input',
    'retention_days': '7',
    'confirm_before_delete': 'False',
    'auto_start': 'False',
    'auto_clean_enabled': 'False',
    'auto_clean_interval': '7'  # 默认每7天自动清理一次（单位：天）
}

class ConfigManager:
    """配置管理类"""

    def __init__(self, config_file='config.ini'):
        base_dir = _get_base_dir()
        self.config_file = Path(base_dir) / config_file
        self.config = configparser.ConfigParser()
        
    def load_config(self):
        """
        加载配置
        
        逻辑：
        - 如果 config.ini 存在且格式正确，读取并返回
        - 如果 config.ini 不存在或格式错误，使用默认配置并创建文件
        """
        if not self.config_file.exists():
            logger.info("配置文件不存在，使用默认配置")
            return self._create_default_config()
            
        try:
            self.config.read(self.config_file, encoding='utf-8')
            
            # 检查是否有 Settings 段
            if 'Settings' not in self.config:
                logger.warning("配置文件格式不正确，缺少 [Settings] 段，使用默认配置")
                return self._create_default_config()
                
            # 读取配置，缺失的项使用默认值
            config = {}
            for key, default_value in DEFAULT_CONFIG.items():
                value = self.config.get('Settings', key, fallback=default_value)
                config[key] = value
                logger.debug(f"读取配置: {key} = {value}")
            
            logger.info(f"配置加载成功: {self.config_file}")
            return config
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            return self._create_default_config()
    
    def save_config(self, config):
        """保存配置到文件"""
        try:
            self.config['Settings'] = {}
            for key, value in config.items():
                self.config['Settings'][key] = str(value)
                
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
            
            logger.info(f"配置保存成功: {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False
    
    def _create_default_config(self):
        """创建默认配置文件并返回默认配置"""
        logger.info("创建默认配置文件...")
        self.save_config(DEFAULT_CONFIG.copy())
        return DEFAULT_CONFIG.copy()
