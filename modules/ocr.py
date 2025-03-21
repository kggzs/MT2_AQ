# -*- coding: utf-8 -*-
import os
import base64
import urllib.parse
import requests
from requests.exceptions import Timeout

from .logger import logger
from .config_manager import config_manager

class OCRManager:
    """OCR管理类，负责验证码识别"""
    _instance = None  # 单例模式实例
    
    def __new__(cls):
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super(OCRManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化OCR管理器"""
        if self._initialized:
            return
            
        # 获取API配置
        self.api_key = config_manager.get('api', 'baidu_ocr', {}).get('api_key', '')
        self.secret_key = config_manager.get('api', 'baidu_ocr', {}).get('secret_key', '')
        self.request_timeout = config_manager.get('request', 'timeout', 30)
        self.max_retries = config_manager.get('request', 'max_retries', 3)
        self.retry_delay = config_manager.get('request', 'retry_delay', 3)
        
        self._initialized = True
    
    def get_access_token(self):
        """获取百度OCR API的access_token"""
        for attempt in range(self.max_retries):
            try:
                url = "https://aip.baidubce.com/oauth/2.0/token"
                params = {"grant_type": "client_credentials", "client_id": self.api_key, "client_secret": self.secret_key}
                response = requests.post(url, params=params, timeout=self.request_timeout)
                if response.status_code != 200 or "access_token" not in response.json():
                    logger.error(f"获取access_token失败: {response.text}")
                    continue
                return str(response.json().get("access_token"))
            except Timeout:
                logger.warning(f"获取access_token超时，第{attempt+1}次尝试")
            except Exception as e:
                logger.error(f"获取access_token出错: {str(e)}")
                
            # 如果不是最后一次尝试，则等待后重试
            if attempt < self.max_retries - 1:
                import time
                time.sleep(self.retry_delay)
                
        logger.error(f"获取access_token失败，已达到最大重试次数")
        return None

    def recognize_captcha(self, image_path):
        """识别验证码
        
        Args:
            image_path: 验证码图片路径
            
        Returns:
            str: 识别结果，失败返回None
        """
        try:
            # 获取access_token
            access_token = self.get_access_token()
            if not access_token:
                return None
                
            url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic?access_token={access_token}"
            
            # 读取图片并转为base64
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf8")
                image_data = urllib.parse.quote_plus(image_data)
            
            # 构建请求
            payload = f'image={image_data}&detect_direction=false&paragraph=false&probability=false'
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            # 发送请求
            response = requests.request("POST", url, headers=headers, data=payload.encode("utf-8"), timeout=self.request_timeout)
            result = response.json()
            
            # 解析结果
            if 'words_result' not in result or not result['words_result']:
                logger.error(f"验证码识别失败: {result}")
                return None
                
            captcha_text = result['words_result'][0]['words']
            # 清理验证码文本，移除空格和特殊字符
            import re
            captcha_text = re.sub(r'[\s+]', '', captcha_text)
            # 确保验证码只包含字母和数字
            captcha_text = re.sub(r'[^a-zA-Z0-9]', '', captcha_text)
            logger.info(f"验证码识别结果: {captcha_text}")
            return captcha_text
        except Timeout:
            logger.error(f"验证码识别请求超时")
            return None
        except Exception as e:
            logger.error(f"验证码识别过程出错: {str(e)}")
            return None

# 创建全局OCR管理器实例
ocr_manager = OCRManager()
