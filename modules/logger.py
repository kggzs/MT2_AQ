# -*- coding: utf-8 -*-
import os
import logging
from datetime import datetime
from .config_manager import config_manager

class LoggerManager:
    """日志管理类，负责配置和管理日志记录"""
    _instance = None  # 单例模式实例
    _logger = None    # 日志记录器
    
    def __new__(cls):
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化日志管理器"""
        if self._initialized:
            return
            
        self._initialized = True
        self.setup_logger()
    
    def setup_logger(self):
        """配置日志记录器"""
        # 获取日志目录配置
        logs_dir = config_manager.get('paths', 'logs_dir', 'logs')
        
        # 创建日志目录
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        # 获取当前日期作为日志文件名
        current_date = datetime.now().strftime("%Y-%m-%d")
        log_file = f'{logs_dir}/mt_sign_{current_date}.log'
        
        # 配置日志格式
        logger = logging.getLogger('mt_sign')
        logger.setLevel(logging.INFO)
        
        # 防止重复添加处理器
        if not logger.handlers:
            # 文件处理器
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # 设置日志格式
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            # 添加处理器
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        self._logger = logger
    
    def get_logger(self):
        """获取日志记录器"""
        return self._logger

# 创建全局日志管理器实例
logger_manager = LoggerManager()
logger = logger_manager.get_logger()
