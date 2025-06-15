#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Debug信息管理器
负责收集、存储和提供前台页面的debug信息显示功能
"""

import time
import threading
from typing import Dict, List, Optional

class DebugManager:
    """Debug信息管理器"""
    
    def __init__(self):
        """初始化debug管理器"""
        self.debug_store: Dict[str, List[Dict]] = {}
        self.lock = threading.Lock()
        self.max_messages_per_session = 100
    
    def store_debug_info(self, session_id: str, message: str, level: str = "INFO"):
        """
        存储debug信息
        
        Args:
            session_id: 会话ID
            message: debug消息
            level: 日志级别 (INFO, WARNING, ERROR)
        """
        with self.lock:
            if session_id not in self.debug_store:
                self.debug_store[session_id] = []
            
            self.debug_store[session_id].append({
                'timestamp': time.time(),
                'level': level,
                'message': message,
                'time_str': time.strftime('%H:%M:%S', time.localtime())
            })
            
            # 限制每个会话最多存储指定数量的debug信息
            if len(self.debug_store[session_id]) > self.max_messages_per_session:
                self.debug_store[session_id] = self.debug_store[session_id][-self.max_messages_per_session:]
    
    def get_debug_info(self, session_id: str, since: float = 0) -> Dict:
        """
        获取debug信息
        
        Args:
            session_id: 会话ID
            since: 获取指定时间戳之后的信息
            
        Returns:
            包含debug信息的字典
        """
        with self.lock:
            if session_id not in self.debug_store:
                return {
                    "session_id": session_id,
                    "debug_info": [],
                    "last_timestamp": 0
                }
            
            debug_info = self.debug_store[session_id]
            
            # 如果指定了since参数，只返回该时间戳之后的信息
            if since > 0:
                debug_info = [info for info in debug_info if info['timestamp'] > since]
            
            return {
                "session_id": session_id,
                "debug_info": debug_info,
                "last_timestamp": debug_info[-1]['timestamp'] if debug_info else 0
            }
    
    def clear_session(self, session_id: str):
        """
        清除指定会话的debug信息
        
        Args:
            session_id: 会话ID
        """
        with self.lock:
            if session_id in self.debug_store:
                del self.debug_store[session_id]
    
    def get_all_sessions(self) -> List[str]:
        """
        获取所有活跃的会话ID
        
        Returns:
            会话ID列表
        """
        with self.lock:
            return list(self.debug_store.keys())
    
    def cleanup_old_sessions(self, max_age: int = 3600):
        """
        清理过期的会话信息
        
        Args:
            max_age: 最大保存时间（秒），默认1小时
        """
        current_time = time.time()
        
        with self.lock:
            sessions_to_remove = []
            
            for session_id, debug_info in self.debug_store.items():
                if debug_info:
                    last_timestamp = debug_info[-1]['timestamp']
                    if current_time - last_timestamp > max_age:
                        sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del self.debug_store[session_id]
    
    def create_debug_callback(self, session_id: str):
        """
        创建debug回调函数，用于爬虫模块
        
        Args:
            session_id: 会话ID
            
        Returns:
            debug回调函数
        """
        def debug_callback(message: str, level: str = "INFO"):
            self.store_debug_info(session_id, message, level)
        
        return debug_callback

# 全局debug管理器实例
debug_manager = DebugManager() 