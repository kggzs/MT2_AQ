# -*- coding: utf-8 -*-
import os
import json
import logging

class ConfigManager:
    """配置管理类，负责加载和管理配置信息"""
    _instance = None  # 单例模式实例
    _config = None    # 配置缓存
    
    def __new__(cls):
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化配置管理器"""
        if self._initialized:
            return
            
        self.logger = logging.getLogger('mt_sign')
        self.config_file = 'config.json'
        self._initialized = True
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        # 定义默认配置
        default_config = {
            "api": {
                "baidu_ocr": {
                    "api_key": "你的百度OCR API Key",
                    "secret_key": "你的百度OCR Secret Key"
                }
            },
            "request": {
                "timeout": 30,
                "max_retries": 3,
                "retry_delay": 3,
                "captcha_max_attempts": 3
            },
            "paths": {
                "accounts_file": "accounts.json",
                "cookies_dir": "cookies",
                "logs_dir": "logs",
                "history_file": "sign_history.json"
            },
            "sign": {
                "account_delay": {
                    "min": 5,
                    "max": 10
                },
                "error_delay": {
                    "min": 10,
                    "max": 15
                }
            }
        }
        
        try:
            # 如果配置文件不存在，创建默认配置文件
            if not os.path.exists(self.config_file):
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, ensure_ascii=False, indent=4)
                self._config = default_config
                return
                
            # 读取现有配置文件
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
                
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {str(e)}，将使用默认配置")
            self._config = default_config
    
    def get_config(self):
        """获取完整配置"""
        return self._config
    
    def get(self, section, key=None, default=None):
        """获取指定配置项
        
        Args:
            section: 配置节名称
            key: 配置项名称，如果为None则返回整个节
            default: 默认值，当配置项不存在时返回
        
        Returns:
            配置值或默认值
        """
        try:
            if section not in self._config:
                return default
                
            if key is None:
                return self._config[section]
                
            if key not in self._config[section]:
                return default
                
            return self._config[section][key]
        except Exception as e:
            self.logger.error(f"获取配置项失败: {str(e)}")
            return default
    
    def save_config(self, config=None):
        """保存配置到文件
        
        Args:
            config: 要保存的配置，如果为None则保存当前配置
            
        Returns:
            bool: 是否保存成功
        """
        try:
            if config is not None:
                self._config = config
                
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {str(e)}")
            return False

# 创建全局配置管理器实例
config_manager = ConfigManager()
