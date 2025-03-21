# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime
from .logger import logger
from .config_manager import config_manager

class HistoryManager:
    """历史记录管理类，负责管理签到历史记录"""
    _instance = None  # 单例模式实例
    _history_data = None  # 历史数据缓存
    
    def __new__(cls):
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super(HistoryManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化历史记录管理器"""
        if self._initialized:
            return
            
        # 获取历史记录文件路径
        self.history_file = config_manager.get('paths', 'history_file', 'sign_history.json')
        self._initialized = True
        self._history_data = self.load_history()
    
    def load_history(self):
        """加载历史记录"""
        try:
            if not os.path.exists(self.history_file):
                # 如果历史记录文件不存在，创建空记录
                default_history = {
                    "accounts": {},
                    "summary": {}
                }
                with open(self.history_file, 'w', encoding='utf-8') as f:
                    json.dump(default_history, f, ensure_ascii=False, indent=4)
                return default_history
                
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
                
            return history
        except Exception as e:
            logger.error(f"加载历史记录失败: {str(e)}")
            # 返回空记录
            return {"accounts": {}, "summary": {}}
    
    def save_history(self):
        """保存历史记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self._history_data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            logger.error(f"保存历史记录失败: {str(e)}")
            return False
    
    def add_sign_record(self, username, sign_data):
        """添加签到记录"""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # 确保账号记录存在
            if username not in self._history_data["accounts"]:
                self._history_data["accounts"][username] = {
                    "history": [],
                    "last_sign": "",
                    "consecutive_days": 0,
                    "total_days": 0
                }
            
            # 添加签到记录
            record = {
                "date": current_date,
                "time": current_time,
                "status": sign_data.get("status", "unknown"),
                "consecutive_days": int(sign_data.get("连续签到", 0)),
                "rank": int(sign_data.get("签到排名", 0)),
                "level": int(sign_data.get("签到等级", 0)),
                "reward": int(sign_data.get("积分奖励", 0)),
                "total_days": int(sign_data.get("总天数", 0))
            }
            
            # 更新账号信息
            self._history_data["accounts"][username]["history"].append(record)
            self._history_data["accounts"][username]["last_sign"] = current_date
            self._history_data["accounts"][username]["consecutive_days"] = int(sign_data.get("连续签到", 0))
            self._history_data["accounts"][username]["total_days"] = int(sign_data.get("总天数", 0))
            
            # 保存历史记录
            self.save_history()
            return True
        except Exception as e:
            logger.error(f"添加签到记录失败: {str(e)}")
            return False
    
    def add_daily_summary(self, summary_data):
        """添加每日签到汇总"""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            # 添加每日汇总
            self._history_data["summary"][current_date] = summary_data
            
            # 保存历史记录
            self.save_history()
            return True
        except Exception as e:
            logger.error(f"添加每日汇总失败: {str(e)}")
            return False
    
    def get_account_history(self, username):
        """获取账号签到历史"""
        try:
            if username in self._history_data["accounts"]:
                return self._history_data["accounts"][username]
            return None
        except Exception as e:
            logger.error(f"获取账号历史失败: {str(e)}")
            return None
    
    def get_daily_summary(self, date=None):
        """获取每日签到汇总"""
        try:
            if date is None:
                date = datetime.now().strftime("%Y-%m-%d")
                
            if date in self._history_data["summary"]:
                return self._history_data["summary"][date]
            return None
        except Exception as e:
            logger.error(f"获取每日汇总失败: {str(e)}")
            return None

# 创建全局历史记录管理器实例
history_manager = HistoryManager()
