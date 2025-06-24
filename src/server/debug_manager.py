#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Debug信息管理器
用于存储和管理搜索过程中的调试信息
"""

import time
import threading
from typing import Dict, List, Any
from datetime import datetime

class DebugManager:
    """Debug信息管理器"""
    
    def __init__(self):
        """初始化Debug管理器"""
        self._debug_data = {}  # 存储debug信息
        self._lock = threading.Lock()  # 线程锁
        
    def store_debug_info(self, session_id: str, message: str, level: str = "INFO"):
        """
        存储Debug信息
        
        Args:
            session_id: 会话ID
            message: 调试信息
            level: 日志级别 (INFO, WARNING, ERROR, DEBUG)
        """
        with self._lock:
            if session_id not in self._debug_data:
                self._debug_data[session_id] = []
            
            debug_item = {
                'timestamp': time.time(),
                'time_str': datetime.now().strftime("%H:%M:%S"),
                'message': message,
                'level': level.upper()
            }
            
            self._debug_data[session_id].append(debug_item)
            
            # 限制每个会话最多保存1000条debug信息
            if len(self._debug_data[session_id]) > 1000:
                self._debug_data[session_id] = self._debug_data[session_id][-500:]
    
    def get_debug_info(self, session_id: str, since: float = 0) -> Dict[str, Any]:
        """
        获取Debug信息
        
        Args:
            session_id: 会话ID
            since: 获取指定时间戳之后的信息
            
        Returns:
            包含debug信息的字典
        """
        with self._lock:
            if session_id not in self._debug_data:
                return {
                    'debug_info': [],
                    'last_timestamp': since,
                    'total_count': 0
                }
            
            # 过滤指定时间戳之后的信息
            debug_info = [
                item for item in self._debug_data[session_id]
                if item['timestamp'] > since
            ]
            
            last_timestamp = max(
                [item['timestamp'] for item in debug_info],
                default=since
            )
            
            return {
                'debug_info': debug_info,
                'last_timestamp': last_timestamp,
                'total_count': len(self._debug_data[session_id])
            }
    
    def clear_debug_info(self, session_id: str):
        """
        清除指定会话的Debug信息
        
        Args:
            session_id: 会话ID
        """
        with self._lock:
            if session_id in self._debug_data:
                del self._debug_data[session_id]
    
    def get_all_sessions(self) -> List[str]:
        """
        获取所有会话ID
        
        Returns:
            会话ID列表
        """
        with self._lock:
            return list(self._debug_data.keys())
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """
        清理超过指定时间的旧会话
        
        Args:
            max_age_hours: 最大保存时间（小时）
        """
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        with self._lock:
            sessions_to_remove = []
            
            for session_id, debug_items in self._debug_data.items():
                if not debug_items:
                    sessions_to_remove.append(session_id)
                    continue
                
                # 检查最新的debug信息时间
                latest_timestamp = max(item['timestamp'] for item in debug_items)
                if current_time - latest_timestamp > max_age_seconds:
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del self._debug_data[session_id]
            
            return len(sessions_to_remove)
    
    def create_debug_callback(self, session_id: str):
        """
        创建Debug回调函数
        
        Args:
            session_id: 会话ID
            
        Returns:
            回调函数
        """
        def debug_callback(message: str, level: str = "INFO"):
            """Debug回调函数"""
            self.store_debug_info(session_id, message, level)
        
        return debug_callback

# 全局debug管理器实例
debug_manager = DebugManager() 