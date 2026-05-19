"""
单实例控制模块
使用QSharedMemory确保程序只能运行一个实例
"""
from PyQt6.QtCore import QSharedMemory, QCoreApplication
from PyQt6.QtWidgets import QMessageBox

class SingleInstance:
    """单实例控制类"""
    
    def __init__(self, app_id='FileCleanerApp'):
        self.app_id = app_id
        self.shared_memory = QSharedMemory(app_id)
        
    def is_already_running(self):
        """检查是否已有实例运行"""
        # 尝试创建共享内存
        if not self.shared_memory.create(1):
            # 创建失败，说明已存在实例
            return True
        return False
    
    def release(self):
        """释放共享内存"""
        if self.shared_memory.isAttached():
            self.shared_memory.detach()
    
    @staticmethod
    def check_and_show_message(parent=None):
        """检查单实例并显示提示"""
        instance = SingleInstance()
        if instance.is_already_running():
            QMessageBox.warning(parent, "提示", "程序已打开")
            return False
        return True
