"""
主窗口UI模块
使用PyQt6实现图形界面
"""
import os
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QCheckBox, QTextEdit, QFileDialog, QMessageBox,
    QStatusBar, QSystemTrayIcon, QMenu, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QTextCursor, QIcon, QAction

from config_manager import ConfigManager
from file_operations import scan_files, delete_files
from autostart_manager import enable_autostart, disable_autostart, is_autostart_enabled
import logging

logger = logging.getLogger('FileCleaner')

class CleanThread(QThread):
    """清理文件的后台线程"""
    log_signal = pyqtSignal(str, str)  # (message, level)
    finished_signal = pyqtSignal(dict)  # result
    
    def __init__(self, directory, retention_days, confirm_before_delete):
        super().__init__()
        self.directory = directory
        self.retention_days = retention_days
        self.confirm_before_delete = confirm_before_delete
        
    def run(self):
        """执行清理操作"""
        try:
            # 扫描文件
            self.log_signal.emit(f"正在扫描目录: {self.directory}", "INFO")
            files_to_delete, scan_stats = scan_files(self.directory, self.retention_days)
            
            self.log_signal.emit(f"扫描完成 - 总计: {scan_stats['total']} 文件, 将删除: {scan_stats['to_delete']}, 保留: {scan_stats['to_keep']}", "INFO")
            
            if not files_to_delete:
                self.log_signal.emit("没有找到需要删除的文件", "INFO")
                self.finished_signal.emit({'success': 0, 'failed': 0, 'failed_files': []})
                return
            
            self.log_signal.emit(f"开始删除 {len(files_to_delete)} 个文件...", "INFO")
            
            # 删除文件
            result = delete_files(files_to_delete, self.confirm_before_delete)
            self.finished_signal.emit(result)
            
        except Exception as e:
            self.log_signal.emit(f"清理过程出错: {e}", "ERROR")
            import traceback
            self.log_signal.emit(traceback.format_exc(), "ERROR")
            self.finished_signal.emit({'success': 0, 'failed': 0, 'failed_files': []})

class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.clean_thread = None
        self.is_cleaning = False
        self.auto_clean_enabled = False  # 自动清理开关状态
        self.auto_clean_timer = QTimer()  # 每小时触发一次的定时器
        self.auto_clean_timer.timeout.connect(self.on_auto_clean_tick)
        self._auto_clean_hours_remaining = 0  # 剩余小时数计数器
        
        self.init_ui()
        self.load_config_to_ui()
        self.init_tray_icon()  # 初始化系统托盘
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("文件清理工具")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 块2：目录配置区域
        dir_layout = QHBoxLayout()
        dir_label = QLabel("目标目录:")
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText(r"C:\zl_robot\input")
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self.browse_directory)
        save_btn = QPushButton("保存配置")
        save_btn.clicked.connect(self.save_config)
        
        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self.dir_input, 1)
        dir_layout.addWidget(browse_btn)
        dir_layout.addWidget(save_btn)
        main_layout.addLayout(dir_layout)
        
        # 块3：过滤条件区域
        filter_layout = QHBoxLayout()
        filter_label = QLabel("保留天数:")
        self.days_combo = QComboBox()
        self.days_combo.addItems(["1", "3", "7", "14"])
        self.days_combo.setCurrentText("7")
        filter_info = QLabel("超过选定天数的文件将被删除")
        filter_info.setStyleSheet("color: gray;")
        
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.days_combo)
        filter_layout.addWidget(filter_info)
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)
        
        # 块4：选项配置区域
        options_layout = QHBoxLayout()
        self.confirm_checkbox = QCheckBox("删除前确认")
        self.autostart_checkbox = QCheckBox("开机自启动")
        
        # 根据注册表状态设置开机自启复选框
        self.autostart_checkbox.setChecked(is_autostart_enabled())
        
        # 连接信号
        self.confirm_checkbox.stateChanged.connect(self.on_confirm_changed)
        self.autostart_checkbox.stateChanged.connect(self.on_autostart_changed)
        
        options_layout.addWidget(self.confirm_checkbox)
        options_layout.addWidget(self.autostart_checkbox)
        options_layout.addStretch()
        main_layout.addLayout(options_layout)
        
        # 块5：自动清理开关区域
        clean_layout = QHBoxLayout()
        clean_layout.setSpacing(12)

        self.clean_toggle_btn = QPushButton("开启清理")
        self.clean_toggle_btn.clicked.connect(self.toggle_auto_clean)
        self.clean_toggle_btn.setFixedSize(100, 32)
        self.clean_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        # 开启 - 绿色扁平
        self.toggle_on_style = """
            QPushButton {
                background: #10B981;
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 13px;
                padding: 0;
            }
            QPushButton:hover { background: #059669; }
            QPushButton:pressed { background: #047857; }
        """
        # 关闭 - 浅靛蓝
        self.toggle_off_style = """
            QPushButton {
                background: #EEF2FF;
                color: #818CF8;
                border: 1px solid #E0E7FF;
                border-radius: 16px;
                font-size: 13px;
                padding: 0;
            }
            QPushButton:hover { background: #E0E7FF; color: #6366F1; }
            QPushButton:pressed { background: #C7D2FE; }
        """
        self.clean_toggle_btn.setStyleSheet(self.toggle_off_style)

        interval_label = QLabel("间隔:")
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["1天", "7天", "15天", "30天(一个月)"])
        self.interval_combo.setCurrentText("7天")
        self.interval_combo.setToolTip("每隔多久自动执行一次清理")
        self.interval_combo.currentTextChanged.connect(self.on_interval_changed)
        interval_unit = QLabel("(自动清理频率)")

        clean_layout.addStretch()
        clean_layout.addWidget(self.clean_toggle_btn)
        clean_layout.addWidget(interval_label)
        clean_layout.addWidget(self.interval_combo)
        clean_layout.addWidget(interval_unit)
        clean_layout.addStretch()
        main_layout.addLayout(clean_layout)
        
        # 块6：日志显示区域
        log_label = QLabel("操作日志")
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(200)
        
        main_layout.addWidget(log_label)
        main_layout.addWidget(self.log_text)
        
        # 块7：状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
    def init_tray_icon(self):
        """初始化系统托盘图标"""
        # 获取图标路径（兼容开发环境和PyInstaller打包后）
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(sys._MEIPASS, "resources", "app.ico")
        else:
            icon_path = str(Path(__file__).parent / "resources" / "app.ico")

        if os.path.exists(icon_path):
            self.tray_icon = QIcon(str(icon_path))
        else:
            # 如果图标不存在，使用默认图标
            from PyQt6.QtWidgets import QStyle
            self.tray_icon = QApplication.style().standardIcon(
                QStyle.StandardPixmap.SP_TrashIcon
            )
        
        # 创建系统托盘
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.tray_icon)
        self.tray.setToolTip("文件清理工具 - 单击显示/隐藏窗口")
        self.tray.activated.connect(self.on_tray_activated)
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("隐藏窗口", self)
        hide_action.triggered.connect(self.hide_window)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("退出程序", self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)
        
        self.tray.setContextMenu(tray_menu)
        self.tray.show()
        logger.info("系统托盘已初始化")
    
    def on_tray_activated(self, reason):
        """托盘图标激活事件（单击显示/隐藏）"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide_window()
            else:
                self.show_window()
    
    def show_window(self):
        """显示主窗口"""
        self.showNormal()
        self.activateWindow()
        self.raise_()
        logger.info("窗口已显示")
    
    def hide_window(self):
        """隐藏主窗口到托盘"""
        self.hide()
        logger.info("窗口已最小化到托盘")
        
    def browse_directory(self):
        """浏览并选择目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择目录", self.dir_input.text() or "C:/"
        )
        if directory:
            self.dir_input.setText(directory)
            
    def load_config_to_ui(self):
        """将配置加载到UI"""
        self.dir_input.setText(self.config.get('directory_path', r'C:\zl_robot\input'))

        retention_days = self.config.get('retention_days', '7')
        index = self.days_combo.findText(retention_days)
        if index >= 0:
            self.days_combo.setCurrentIndex(index)

        confirm = self.config.get('confirm_before_delete', 'False').lower() == 'true'
        self.confirm_checkbox.setChecked(confirm)

        # 自动清理开关
        auto_clean = self.config.get('auto_clean_enabled', 'False').lower() == 'true'
        self.auto_clean_enabled = auto_clean
        if auto_clean:
            self.clean_toggle_btn.setText("关闭清理")
            self.clean_toggle_btn.setStyleSheet(self.toggle_on_style)
            # 启动定时器
            interval_days = int(self.config.get('auto_clean_interval', '7'))
            self._start_auto_timer(interval_days)
            self.status_bar.showMessage(f"自动清理运行中 (间隔{interval_days}天)")
            self.execute_auto_clean()
        else:
            self.clean_toggle_btn.setText("开启清理")
            self.clean_toggle_btn.setStyleSheet(self.toggle_off_style)

        # 清理间隔
        interval = self.config.get('auto_clean_interval', '7')
        # 映射：数字 -> 下拉框文字
        interval_map = {'1': '1天', '7': '7天', '15': '15天', '30': '30天(一个月)'}
        interval_text = interval_map.get(str(interval), '7天')
        idx = self.interval_combo.findText(interval_text)
        if idx >= 0:
            self.interval_combo.setCurrentIndex(idx)
        
    def save_config(self):
        """保存配置"""
        self.config['directory_path'] = self.dir_input.text()
        self.config['retention_days'] = self.days_combo.currentText()
        self.config['confirm_before_delete'] = str(self.confirm_checkbox.isChecked())
        self.config['auto_start'] = str(self.autostart_checkbox.isChecked())
        self.config['auto_clean_enabled'] = str(self.auto_clean_enabled)
        self.config['auto_clean_interval'] = str(self._get_interval_days())
        
        if self.config_manager.save_config(self.config):
            self.log_message("配置保存成功", "INFO")
            QMessageBox.information(self, "成功", "配置已保存")
        else:
            self.log_message("配置保存失败", "ERROR")
            QMessageBox.warning(self, "失败", "配置保存失败")
            
    def on_confirm_changed(self, state):
        """删除前确认选项变化"""
        self.config['confirm_before_delete'] = str(bool(state))
        self.config_manager.save_config(self.config)
        
    def on_autostart_changed(self, state):
        """开机自启选项变化"""
        if state:
            if enable_autostart():
                self.log_message("已启用开机自启", "INFO")
            else:
                self.log_message("启用开机自启失败", "ERROR")
                self.autostart_checkbox.setChecked(False)
        else:
            if disable_autostart():
                self.log_message("已禁用开机自启", "INFO")
            else:
                self.log_message("禁用开机自启失败", "ERROR")
                self.autostart_checkbox.setChecked(True)
                
    def toggle_auto_clean(self):
        """切换自动清理开关"""
        self.auto_clean_enabled = not self.auto_clean_enabled

        if self.auto_clean_enabled:
            # 开启自动清理
            self.clean_toggle_btn.setText("关闭清理")
            self.clean_toggle_btn.setStyleSheet(self.toggle_on_style)
            self.status_bar.showMessage("自动清理已开启")
            self.log_message(f"✓ 自动清理已开启 (间隔: {self.interval_combo.currentText()})", "INFO")

            # 立即执行一次清理（首次）
            self.execute_auto_clean()

            # 启动定时器
            interval_days = self._get_interval_days()
            self._start_auto_timer(interval_days)

        else:
            # 关闭自动清理
            self.clean_toggle_btn.setText("开启清理")
            self.clean_toggle_btn.setStyleSheet(self.toggle_off_style)
            self.auto_clean_timer.stop()
            self.status_bar.showMessage("自动清理已关闭")
            self.log_message("自动清理已关闭", "INFO")

        # 保存状态到配置
        self.config['auto_clean_enabled'] = str(self.auto_clean_enabled)
        self.config_manager.save_config(self.config)

    def _get_interval_days(self):
        """从下拉框获取天数"""
        text = self.interval_combo.currentText()
        # "1天" -> 1, "7天" -> 7, "15天" -> 15, "30天(一个月)" -> 30
        return int(text.replace('天', '').replace('(一个月)', ''))

    def on_interval_changed(self, text):
        """清理间隔变更时重新设置定时器"""
        interval = self._get_interval_days()
        self.config['auto_clean_interval'] = str(interval)
        self.config_manager.save_config(self.config)
        logger.info(f"自动清理间隔变更为 {interval} 天")

        # 如果定时器正在运行，重置倒计时
        if self.auto_clean_timer.isActive():
            self._auto_clean_hours_remaining = interval * 24
            self.log_message(f"清理间隔已更新为 {text}", "INFO")

    def execute_auto_clean(self):
        """执行一次清理操作"""
        if self.is_cleaning:
            self.log_message("上次清理尚未完成，跳过本次", "WARNING")
            return

        directory = self.dir_input.text().strip()

        if not directory or not os.path.exists(directory):
            self.log_message(f"目录无效或不存在，跳过: {directory}", "ERROR")
            return

        retention_days = int(self.days_combo.currentText())

        self.is_cleaning = True
        self.status_bar.showMessage("正在清理...")

        self.clean_thread = CleanThread(
            directory,
            retention_days,
            False  # 自动模式下不弹确认框
        )
        self.clean_thread.log_signal.connect(self.log_message)
        self.clean_thread.finished_signal.connect(self.on_clean_finished)
        self.clean_thread.start()

    def _start_auto_timer(self, days):
        """启动每小时触发一次的自动清理计时器"""
        self._auto_clean_hours_remaining = days * 24
        self.auto_clean_timer.start(3600000)  # 每小时触发一次（毫秒）
        logger.info(f"自动清理计时器已启动，剩余 {self._auto_clean_hours_remaining} 小时")

    def on_auto_clean_tick(self):
        """每小时定时器触发，倒计时归零时执行清理"""
        if not self.auto_clean_enabled:
            return

        self._auto_clean_hours_remaining -= 1

        if self._auto_clean_hours_remaining <= 0:
            # 倒计时结束，执行清理并重置
            self.log_message("=== 定时清理触发 ===", "INFO")
            self.execute_auto_clean()
            # 重置计数器
            self._auto_clean_hours_remaining = self._get_interval_days() * 24
            logger.info(f"计时器重置，剩余 {self._auto_clean_hours_remaining} 小时")

    def on_clean_finished(self, result):
        """清理完成回调"""
        self.is_cleaning = False
        success = result.get('success', 0)
        failed = result.get('failed', 0)

        if failed > 0:
            self.status_bar.showMessage(f"清理完成 - 成功:{success} 失败:{failed}")
        else:
            self.status_bar.showMessage(f"清理完成 - 删除了 {success} 个文件")

        self.log_message(f"清理完成 - 成功: {success}, 失败: {failed}", "INFO")
        
        if failed > 0:
            failed_files = result.get('failed_files', [])
            self.log_message(f"失败文件数: {len(failed_files)}", "WARNING")
            
    def log_message(self, message, level="INFO"):
        """添加日志消息到文本框"""
        color_map = {
            "INFO": "black",
            "WARNING": "orange",
            "ERROR": "red"
        }
        color = color_map.get(level, "black")
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        formatted_message = f"[{timestamp}] [{level}] {message}"
        
        self.log_text.append(f'<span style="color: {color};">{formatted_message}</span>')
        
        # 滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
        
        # 同时记录到logger
        if level == "INFO":
            logger.info(message)
        elif level == "WARNING":
            logger.warning(message)
        elif level == "ERROR":
            logger.error(message)
            
    def closeEvent(self, event):
        """窗口关闭事件 - 最小化到系统托盘"""
        # 忽略关闭事件，改为隐藏到托盘
        event.ignore()
        self.hide_window()
        # 显示托盘提示
        self.tray.showMessage(
            "文件清理工具",
            "程序已最小化到系统托盘\n双击图标可恢复窗口",
            QSystemTrayIcon.MessageIcon.Information,
            2000  # 显示2秒
        )
    
    def quit_app(self):
        """真正退出应用程序"""
        self.auto_clean_timer.stop()
        if self.is_cleaning:
            reply = QMessageBox.question(
                None, "确认",
                "清理操作正在进行中，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        logger.info("程序正在退出...")
        self.tray.hide()  # 隐藏托盘图标
        QApplication.quit()
