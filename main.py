"""
程序入口
初始化应用和主窗口
"""
import sys
import os

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon

from single_instance import SingleInstance
from logger import setup_logger
import logging


def get_resource_path(relative_path):
    """
    获取资源文件的绝对路径，同时兼容开发环境和PyInstaller打包后
    - 开发模式: 基于 __file__ 定位
    - 打包模式: 使用 sys._MEIPASS (临时解压目录)
    """
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)


def main():
    """主函数"""
    # 设置日志
    setup_logger()
    logger = logging.getLogger('FileCleaner')

    # 创建QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("文件清理工具")

    # 设置应用图标（兼容开发环境和打包后）
    icon_path = get_resource_path("resources/app.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # 检查单实例
    instance = SingleInstance('FileCleanerApp')
    if instance.is_already_running():
        QMessageBox.warning(None, "提示", "程序已打开")
        sys.exit(0)

    # 导入主窗口（延迟导入以避免单实例问题）
    from main_window import MainWindow

    # 创建主窗口
    window = MainWindow()
    window.show()

    logger.info("程序启动")

    # 启动事件循环
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
