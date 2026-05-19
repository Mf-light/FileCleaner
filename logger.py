"""
日志记录模块
配置logging模块，输出到文件和控制台
日志文件位置：打包后跟随 exe 目录，开发模式跟随脚本目录
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler


def _get_base_dir():
    """获取程序根目录：打包后为 exe 所在目录，开发模式为脚本目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def setup_logger(log_file='app.log', level=logging.INFO):
    """配置日志记录器"""
    base_dir = _get_base_dir()
    log_path = os.path.join(base_dir, log_file)

    # 创建logger
    logger = logging.getLogger('FileCleaner')
    logger.setLevel(level)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 文件handler - 使用RotatingFileHandler限制文件大小
    file_handler = RotatingFileHandler(
        log_path, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    
    # 控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # 格式化
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加handler
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_logger():
    """获取日志记录器"""
    logger = logging.getLogger('FileCleaner')
    if not logger.handlers:
        return setup_logger()
    return logger
