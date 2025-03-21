# -*- coding: utf-8 -*-
import os
import json
from .logger import logger
from .config_manager import config_manager

class AccountManager:
    """账户管理类，负责加载和管理账户信息"""
    _instance = None  # 单例模式实例
    _accounts = None  # 账户缓存
    
    def __new__(cls):
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super(AccountManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化账户管理器"""
        if self._initialized:
            return
            
        # 获取账户配置文件路径
        self.account_file = config_manager.get('paths', 'accounts_file', 'accounts.json')
        self._initialized = True
        self._accounts = self.load_accounts()
    
    def load_accounts(self):
        """从配置文件加载账号信息"""
        try:
            if not os.path.exists(self.account_file):
                # 如果配置文件不存在，创建一个示例配置
                example_accounts = [
                    {"username": "用户名1", "password": "密码1", "questionid": 0, "answer": ""},
                    {"username": "用户名2", "password": "密码2", "questionid": 1, "answer": "安全问题答案"}
                ]
                with open(self.account_file, 'w', encoding='utf-8') as f:
                    json.dump(example_accounts, f, ensure_ascii=False, indent=4)
                logger.warning(f"账号配置文件不存在，已创建示例配置文件: {self.account_file}")
                logger.warning(f"请修改配置文件后重新运行程序")
                return []
                
            with open(self.account_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 直接使用加载的数据作为账号列表
            if not isinstance(data, list):
                logger.error(f"账号配置文件格式错误，应为账号列表格式")
                return []
                
            if not data:
                logger.warning(f"账号配置文件为空，请添加账号信息")
                return []
                
            logger.info(f"成功加载 {len(data)} 个账号")
            return data
        except Exception as e:
            logger.error(f"加载账号配置失败: {str(e)}")
            return []
    
    def get_accounts(self):
        """获取所有账号信息"""
        return self._accounts
    
    def reload_accounts(self):
        """重新加载账号信息"""
        self._accounts = self.load_accounts()
        return self._accounts

# 创建全局账户管理器实例
account_manager = AccountManager()
