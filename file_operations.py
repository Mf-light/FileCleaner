"""
文件操作模块
负责扫描和删除文件
"""
import os
import time
import logging
from pathlib import Path

logger = logging.getLogger('FileCleaner')

def scan_files(directory, retention_days):
    """
    扫描目录，返回需要删除的文件列表
    
    Args:
        directory: 目标目录
        retention_days: 保留天数（只保留此天数内创建的文件）
        
    Returns:
        tuple: (需要删除的文件路径列表, 扫描统计信息字典)
    """
    files_to_delete = []
    files_kept = []
    stats = {'total': 0, 'to_delete': 0, 'to_keep': 0}
    
    # 规范化路径
    directory = Path(directory).resolve()
    
    if not directory.exists():
        logger.error(f"目录不存在: {directory}")
        return files_to_delete, stats
    
    logger.info(f"开始扫描目录: {directory}, 保留最近 {retention_days} 天内创建的文件")
    
    try:
        # 使用os.scandir提升性能
        for entry in os.scandir(directory):
            if not entry.is_file():
                continue
            
            file_path = entry.path
            stats['total'] += 1
            
            try:
                # 获取文件创建时间（Windows上使用创建时间）
                create_time = os.path.getctime(file_path)
                current_time = time.time()
                days_old = (current_time - create_time) / (24 * 3600)
                
                from datetime import datetime
                create_date = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S')
                
                # 如果文件创建时间超过保留天数，添加到删除列表
                # 使用 >= 确保边界条件正确：超过N天的文件都应被删除
                if days_old >= retention_days:
                    files_to_delete.append(file_path)
                    stats['to_delete'] += 1
                    logger.info(f"[将删除] {Path(file_path).name} | 创建时间: {create_date} | {days_old:.1f}天前")
                else:
                    files_kept.append(file_path)
                    stats['to_keep'] += 1
                    logger.debug(f"[保留] {Path(file_path).name} | 创建时间: {create_date} | {days_old:.1f}天前")
                    
            except Exception as e:
                logger.warning(f"无法获取文件时间 {file_path}: {e}")
                
    except Exception as e:
        logger.error(f"扫描目录失败 {directory}: {e}")
    
    logger.info(f"扫描完成 - 总计: {stats['total']} 文件, 将删除: {stats['to_delete']}, 保留: {stats['to_keep']}")
    return files_to_delete, stats

def delete_files(file_list, confirm=True):
    """
    删除文件列表中的文件
    
    Args:
        file_list: 要删除的文件路径列表
        confirm: 是否需要确认（保留参数以兼容旧代码）
        
    Returns:
        dict: 删除结果统计 {'success': 成功数, 'failed': 失败数, 'failed_files': 失败文件列表}
    """
    result = {
        'success': 0,
        'failed': 0,
        'failed_files': []
    }
    
    if not file_list:
        logger.info("没有文件需要删除")
        return result
    
    logger.info(f"开始删除 {len(file_list)} 个文件:")
    for f in file_list:
        logger.info(f"  - {f}")
    
    for file_path in file_list:
        try:
            # 确保文件存在且可删除
            if os.path.exists(file_path):
                os.remove(file_path)
                result['success'] += 1
                logger.info(f"✓ 删除成功: {Path(file_path).name}")
            else:
                logger.warning(f"文件不存在，跳过: {file_path}")
        except PermissionError as e:
            result['failed'] += 1
            result['failed_files'].append(file_path)
            logger.error(f"✗ 权限不足，无法删除: {Path(file_path).name} - {e}")
        except OSError as e:
            result['failed'] += 1
            result['failed_files'].append(file_path)
            logger.error(f"✗ 系统错误，删除失败: {Path(file_path).name} - {e}")
        except Exception as e:
            result['failed'] += 1
            result['failed_files'].append(file_path)
            logger.error(f"✗ 删除失败: {Path(file_path).name} - {e}")
    
    logger.info(f"===== 删除完成 ===== 成功: {result['success']}, 失败: {result['failed']}")
    return result
