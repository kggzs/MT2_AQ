# -*- coding: utf-8 -*-
import os
import re
import time
import json
import random
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException, Timeout, ConnectionError

from .logger import logger
from .config_manager import config_manager
from .history_manager import history_manager
from .ocr import ocr_manager

class DzSigner:
    """论坛签到器，负责执行登录和签到操作"""
    def __init__(self, username, password, questionid=0, answer=""):
        self.username = username
        self.password = password
        self.questionid = questionid  # 安全提问ID
        self.answer = answer  # 安全提问答案
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Origin': 'https://bbs.binmt.cc',
            'Referer': 'https://bbs.binmt.cc/'
        })
        
        # 获取配置参数
        cookies_dir = config_manager.get('paths', 'cookies_dir', 'cookies')
        self.cookie_file = f'{cookies_dir}/{username}_cookies.json'
        self.request_timeout = config_manager.get('request', 'timeout', 30)
        self.max_retries = config_manager.get('request', 'max_retries', 3)
        self.retry_delay = config_manager.get('request', 'retry_delay', 3)
        self.captcha_max_attempts = config_manager.get('request', 'captcha_max_attempts', 3)
        
        # 重试计数器
        self.retry_count = 0
        # 验证码识别尝试次数
        self.captcha_attempts = 0
        # 签到结果
        self.sign_result = {}

    def save_cookies(self):
        """保存Cookie到本地文件"""
        try:
            # 确保cookies目录存在
            cookies_dir = os.path.dirname(self.cookie_file)
            os.makedirs(cookies_dir, exist_ok=True)
            
            with open(self.cookie_file, 'w', encoding='utf-8') as f:
                json.dump(self.session.cookies.get_dict(), f)
            logger.info(f"[{self.username}] Cookie已保存到本地: {self.cookie_file}")
            return True
        except Exception as e:
            logger.error(f"[{self.username}] 保存Cookie失败: {str(e)}")
            return False

    def load_cookies(self):
        """从本地文件加载Cookie"""
        try:
            if not os.path.exists(self.cookie_file):
                logger.info(f"[{self.username}] 未找到Cookie文件，将进行账号登录")
                return False
                
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
                
            for key, value in cookies.items():
                self.session.cookies.set(key, value)
                
            logger.info(f"[{self.username}] 已从本地加载Cookie: {self.cookie_file}")
            return True
        except Exception as e:
            logger.error(f"[{self.username}] 加载Cookie失败: {str(e)}")
            return False

    def check_login_status(self):
        """检查登录状态"""
        try:
            home_page = self.session.get('https://bbs.binmt.cc/', timeout=self.request_timeout)
            # 检查是否包含已登录的标识
            return '访问我的空间' in home_page.text and self.username in home_page.text
        except Timeout:
            logger.error(f"[{self.username}] 检查登录状态超时")
            return False
        except ConnectionError:
            logger.error(f"[{self.username}] 检查登录状态连接错误")
            return False
        except Exception as e:
            logger.error(f"[{self.username}] 检查登录状态失败: {str(e)}")
            return False

    def check_signed(self):
        """检测今日是否已签到"""
        for attempt in range(self.max_retries):
            try:
                sign_page = self.session.get('https://bbs.binmt.cc/k_misign-sign.html', timeout=self.request_timeout)
                soup = BeautifulSoup(sign_page.text, 'html.parser')
                
                if soup.find('span', {'class': 'btnvisted'}):
                    return True
                    
                sign_button = soup.find('a', {'id': 'JD_sign'})
                if not sign_button or 'disabled' in sign_button.get('class', []):
                    return True
                    
                return "今日已签" in sign_page.text
                
            except Timeout:
                logger.warning(f"[{self.username}] 签到状态检测超时，第{attempt+1}次尝试")
            except ConnectionError:
                logger.warning(f"[{self.username}] 签到状态检测连接错误，第{attempt+1}次尝试")
            except Exception as e:
                logger.error(f"[{self.username}] 签到状态检测失败: {str(e)}")
                return False
                
            # 如果不是最后一次尝试，则等待后重试
            if attempt < self.max_retries - 1:
                retry_delay = self.retry_delay + random.uniform(0, 2)  # 添加随机延迟
                logger.info(f"[{self.username}] {retry_delay:.2f}秒后重试...")
                time.sleep(retry_delay)
                
        logger.error(f"[{self.username}] 签到状态检测失败，已达到最大重试次数")
        return False

    def download_captcha(self, soup):
        """下载验证码图片并处理安全提问"""
        for attempt in range(self.max_retries):
            try:
                # 查找验证码图片元素
                captcha_img = soup.find('img', {'src': re.compile(r'misc\.php\?mod=seccode')})
                if not captcha_img:
                    logger.error(f"[{self.username}] 未找到验证码图片")
                    return None
                    
                # 获取验证码图片URL
                captcha_url = 'https://bbs.binmt.cc/' + captcha_img['src']
                
                # 下载验证码图片
                captcha_response = self.session.get(captcha_url, timeout=self.request_timeout)
                if captcha_response.status_code != 200:
                    logger.error(f"[{self.username}] 下载验证码图片失败: {captcha_response.status_code}")
                    if attempt < self.max_retries - 1:
                        logger.info(f"[{self.username}] 第{attempt+1}次尝试下载验证码图片...")
                        time.sleep(self.retry_delay)
                        continue
                    return None
                    
                # 保存验证码图片
                # 为避免多账号同时下载验证码冲突，使用用户名作为文件名前缀
                captcha_path = f'captcha_{self.username}.jpg'
                with open(captcha_path, 'wb') as f:
                    f.write(captcha_response.content)
                    
                logger.info(f"[{self.username}] 验证码图片已保存到: {captcha_path}")
                return captcha_path
            except Timeout:
                logger.warning(f"[{self.username}] 下载验证码图片超时，第{attempt+1}次尝试")
            except ConnectionError:
                logger.warning(f"[{self.username}] 下载验证码图片连接错误，第{attempt+1}次尝试")
            except Exception as e:
                logger.error(f"[{self.username}] 下载验证码图片失败: {str(e)}")
                return None
                
            # 如果不是最后一次尝试，则等待后重试
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay)
                
        logger.error(f"[{self.username}] 下载验证码图片失败，已达到最大重试次数")
        return None

    def login(self):
        """执行登录操作"""
        # 先尝试加载Cookie并检查登录状态
        if self.load_cookies() and self.check_login_status():
            logger.info(f"[{self.username}] 使用Cookie登录成功")
            return True
            
        logger.info(f"[{self.username}] Cookie无效或已过期，将使用账号密码登录")
        
        # 重置验证码尝试次数
        self.captcha_attempts = 0
        
        # 登录重试机制
        for login_attempt in range(self.max_retries):
            try:
                login_page = self.session.get('https://bbs.binmt.cc/member.php?mod=logging&action=login', timeout=self.request_timeout)
                soup = BeautifulSoup(login_page.text, 'html.parser')
                
                username_input = soup.find('input', {'name': 'username'})
                password_input = soup.find('input', {'name': 'password'})
                
                if not username_input or not password_input:
                    logger.error(f"[{self.username}] 找不到登录表单元素")
                    return False

                login_data = {
                    'formhash': soup.find('input', {'name': 'formhash'})['value'],
                    'referer': 'https://bbs.binmt.cc/',
                    'username': self.username,
                    'password': self.password,
                    'cookietime': soup.find('input', {'name': 'cookietime'})['value'],
                    'questionid': str(self.questionid),  # 添加安全提问ID
                    'loginsubmit': '登录'
                }
                
                # 如果设置了安全提问，添加答案
                if self.questionid > 0 and self.answer:
                    login_data['answer'] = self.answer
                    logger.info(f"[{self.username}] 使用安全提问登录，提问ID: {self.questionid}")

                login_data[username_input['id']] = self.username
                login_data[password_input['id']] = self.password

                # 检查是否需要验证码
                seccode_verify = soup.find('input', {'name': 'seccodeverify'})
                if seccode_verify:
                    logger.info(f"[{self.username}] 检测到需要输入验证码 (尝试 {self.captcha_attempts + 1}/{self.captcha_max_attempts})")
                    
                    # 超过最大尝试次数
                    if self.captcha_attempts >= self.captcha_max_attempts:
                        logger.error(f"[{self.username}] 验证码识别已达到最大尝试次数 {self.captcha_max_attempts}")
                        return False
                    
                    self.captcha_attempts += 1
                    
                    # 下载验证码图片
                    captcha_path = self.download_captcha(soup)
                    if not captcha_path:
                        if login_attempt < self.max_retries - 1:
                            logger.warning(f"[{self.username}] 验证码下载失败，{self.retry_delay}秒后重试...")
                            time.sleep(self.retry_delay)
                            continue
                        return False
                        
                    # 识别验证码
                    captcha_text = ocr_manager.recognize_captcha(captcha_path)
                    if not captcha_text:
                        if login_attempt < self.max_retries - 1:
                            logger.warning(f"[{self.username}] 验证码识别失败，{self.retry_delay}秒后重试...")
                            time.sleep(self.retry_delay)
                            continue
                        return False
                        
                    # 添加验证码到登录数据
                    idhash = seccode_verify['id'].replace('seccodeverify_', '')
                    login_data['seccodehash'] = idhash
                    login_data['seccodeverify'] = captcha_text

                # 发送登录请求
                login_res = self.session.post(
                    'https://bbs.binmt.cc/member.php?mod=logging&action=login&loginsubmit=yes&infloat=yes&handlekey=login',
                    data=login_data,
                    timeout=self.request_timeout
                )

                # 检查登录结果
                if '欢迎您回来' in login_res.text or self.check_login_status():
                    logger.info(f"[{self.username}] 登录成功")
                    # 保存Cookie
                    self.save_cookies()
                    return True
                    
                # 如果登录失败，检查是否是验证码错误
                if '验证码错误' in login_res.text and seccode_verify:
                    logger.warning(f"[{self.username}] 验证码识别错误，重新尝试")
                    # 不递归调用，而是继续循环重试
                    continue
                
                # 检查是否是密码错误
                if '密码错误' in login_res.text:
                    logger.error(f"[{self.username}] 登录失败：密码错误")
                    return False
                    
                logger.error(f"[{self.username}] 登录失败，请检查账号密码")
                return False
                
            except Timeout:
                logger.warning(f"[{self.username}] 登录请求超时，第{login_attempt+1}次尝试")
            except ConnectionError:
                logger.warning(f"[{self.username}] 登录连接错误，第{login_attempt+1}次尝试")
            except Exception as e:
                logger.error(f"[{self.username}] 登录过程出现错误: {str(e)}")
                return False
                
            # 如果不是最后一次尝试，则等待后重试
            if login_attempt < self.max_retries - 1:
                retry_delay = self.retry_delay + random.uniform(0, 2)  # 添加随机延迟
                logger.info(f"[{self.username}] {retry_delay:.2f}秒后重试登录...")
                time.sleep(retry_delay)
                
        logger.error(f"[{self.username}] 登录失败，已达到最大重试次数 {self.max_retries}")
        return False

    def get_formhash(self):
        """获取动态formhash值"""
        for attempt in range(self.max_retries):
            try:
                if self.check_signed():
                    logger.info(f"[{self.username}] 今日已完成签到，无需重复操作")
                    return None
                    
                sign_page = self.session.get('https://bbs.binmt.cc/k_misign-sign.html', timeout=self.request_timeout)
                soup = BeautifulSoup(sign_page.text, 'html.parser')
                sign_button = soup.find('a', {'id': 'JD_sign'})
                
                if not sign_button:
                    logger.error(f"[{self.username}] 找不到签到按钮")
                    if attempt < self.max_retries - 1:
                        logger.warning(f"[{self.username}] 第{attempt+1}次尝试获取formhash...")
                        time.sleep(self.retry_delay)
                        continue
                    return None
                    
                formhash_match = re.search(r'formhash=([a-f0-9]+)', sign_button['href'])
                if not formhash_match:
                    logger.error(f"[{self.username}] 无法从签到按钮中提取formhash")
                    if attempt < self.max_retries - 1:
                        logger.warning(f"[{self.username}] 第{attempt+1}次尝试获取formhash...")
                        time.sleep(self.retry_delay)
                        continue
                    return None
                    
                formhash = formhash_match.group(1)
                logger.info(f"[{self.username}] 成功获取formhash: {formhash}")
                return formhash
                
            except Timeout:
                logger.warning(f"[{self.username}] 获取formhash超时，第{attempt+1}次尝试")
            except ConnectionError:
                logger.warning(f"[{self.username}] 获取formhash连接错误，第{attempt+1}次尝试")
            except Exception as e:
                logger.error(f"[{self.username}] 获取formhash失败: {str(e)}")
                return None
                
            # 如果不是最后一次尝试，则等待后重试
            if attempt < self.max_retries - 1:
                retry_delay = self.retry_delay + random.uniform(0, 2)  # 添加随机延迟
                logger.info(f"[{self.username}] {retry_delay:.2f}秒后重试获取formhash...")
                time.sleep(retry_delay)
                
        logger.error(f"[{self.username}] 获取formhash失败，已达到最大重试次数")
        return None

    def sign(self):
        """执行签到操作"""
        if self.check_signed():
            logger.info(f"[{self.username}] 签到状态检测：今日已签到")
            return True

        formhash = self.get_formhash()
        if not formhash:
            return False

        for attempt in range(self.max_retries):
            try:
                logger.info(f"[{self.username}] 正在执行签到操作 (尝试 {attempt+1}/{self.max_retries})")
                res = self.session.get(
                    f'https://bbs.binmt.cc/plugin.php?id=k_misign:sign&operation=qiandao&formhash={formhash}&format=empty',
                    headers={'X-Requested-With': 'XMLHttpRequest'},
                    timeout=self.request_timeout
                )
                
                if res.status_code == 200:
                    # 等待一段时间，确保签到状态更新
                    wait_time = 1.5 + random.uniform(0, 1)  # 添加随机延迟
                    logger.info(f"[{self.username}] 签到请求成功，等待 {wait_time:.2f} 秒后检查签到状态...")
                    time.sleep(wait_time)
                    
                    # 检查签到是否成功
                    if self.check_signed():
                        logger.info(f"[{self.username}] 签到成功确认")
                        return True
                    else:
                        logger.warning(f"[{self.username}] 签到请求已发送，但签到状态未更新")
                        if attempt < self.max_retries - 1:
                            logger.info(f"[{self.username}] 将重试签到操作...")
                            continue
                else:
                    logger.error(f"[{self.username}] 签到请求返回状态码: {res.status_code}")
                    if attempt < self.max_retries - 1:
                        logger.info(f"[{self.username}] 将重试签到操作...")
                        continue
                    
            except Timeout:
                logger.warning(f"[{self.username}] 签到请求超时，第{attempt+1}次尝试")
            except ConnectionError:
                logger.warning(f"[{self.username}] 签到请求连接错误，第{attempt+1}次尝试")
            except Exception as e:
                logger.error(f"[{self.username}] 签到请求失败: {str(e)}")
                return False
                
            # 如果不是最后一次尝试，则等待后重试
            if attempt < self.max_retries - 1:
                retry_delay = self.retry_delay + random.uniform(0, 2)  # 添加随机延迟
                logger.info(f"[{self.username}] {retry_delay:.2f}秒后重试签到...")
                time.sleep(retry_delay)
                
        logger.error(f"[{self.username}] 签到失败，已达到最大重试次数")
        return False
            
    def get_stats(self):
        """获取签到统计数据"""
        for attempt in range(self.max_retries):
            try:
                sign_page = self.session.get('https://bbs.binmt.cc/k_misign-sign.html', timeout=self.request_timeout)
                soup = BeautifulSoup(sign_page.text, 'html.parser')
                
                stats = {}
                stats_fields = {
                    '连续签到': 'lxdays',
                    '签到等级': 'lxlevel',
                    '积分奖励': 'lxreward',
                    '总天数': 'lxtdays',
                    '签到排名': 'qiandaobtnnum'
                }
                
                # 逐个获取统计数据，避免一个字段出错导致整个统计失败
                for label, field_id in stats_fields.items():
                    try:
                        field = soup.find('input', {'id': field_id})
                        if field and 'value' in field.attrs:
                            stats[label] = field['value']
                        else:
                            stats[label] = 'N/A'
                    except Exception as e:
                        logger.warning(f"[{self.username}] 获取{label}失败: {str(e)}")
                        stats[label] = 'N/A'
                
                # 检查是否获取到了所有字段
                if all(value != 'N/A' for value in stats.values()):
                    return stats
                else:
                    logger.warning(f"[{self.username}] 部分统计数据获取失败: {stats}")
                    if attempt < self.max_retries - 1:
                        logger.info(f"[{self.username}] 将重试获取统计数据...")
                        time.sleep(self.retry_delay)
                        continue
                    return stats
                    
            except Timeout:
                logger.warning(f"[{self.username}] 获取统计数据超时，第{attempt+1}次尝试")
            except ConnectionError:
                logger.warning(f"[{self.username}] 获取统计数据连接错误，第{attempt+1}次尝试")
            except Exception as e:
                logger.warning(f"[{self.username}] 获取统计信息失败: {str(e)}")
                return {}
                
            # 如果不是最后一次尝试，则等待后重试
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay)
                
        logger.warning(f"[{self.username}] 获取统计数据失败，已达到最大重试次数")
        return {}

    def run(self):
        """主运行流程"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        logger.info(f"[{self.username}] 开始执行MT论坛自动签到 - {current_date}")
        start_time = time.time()
        
        try:
            # 登录
            logger.info(f"[{self.username}] 正在执行登录...")
            if not self.login():
                logger.error(f"[{self.username}] 登录失败，请检查账号密码或网络连接")
                return False
            
            # 检查是否已签到
            logger.info(f"[{self.username}] 正在检查签到状态...")
            if self.check_signed():
                logger.info(f"[{self.username}] 今日已完成签到，无需重复操作")
            else:
                # 执行签到
                logger.info(f"[{self.username}] 正在执行签到...")
                if not self.sign():
                    logger.warning(f"[{self.username}] 签到未完成，可能出现异常")
                    # 添加失败记录
                    failed_stats = {'status': 'failed'}
                    history_manager.add_sign_record(self.username, failed_stats)
                    return False
                    
            # 获取签到统计信息
            logger.info(f"[{self.username}] === 签到信息 ===")
            stats = self.get_stats()
            if stats:
                # 添加状态标记
                stats['status'] = 'success'
                
                summary_message = (
                    f"连续签到: {stats.get('连续签到', 'N/A')} 天\n"
                    f"今日排名: 第{stats.get('签到排名', 'N/A')} 位\n"
                    f"签到等级: Lv{stats.get('签到等级', 'N/A')}\n"
                    f"本次积分: +{stats.get('积分奖励', 'N/A')}\n"
                    f"总签到天数: {stats.get('总天数', 'N/A')} 天"
                )
                logger.info(f"[{self.username}] {summary_message}")
                
                # 添加到历史记录
                history_manager.add_sign_record(self.username, stats)
            
            # 计算耗时
            elapsed_time = time.time() - start_time
            logger.info(f"[{self.username}] 签到任务完成，耗时: {elapsed_time:.2f}秒")
            return True
                
        except Exception as e:
            logger.error(f"[{self.username}] 签到过程出现未处理的异常: {str(e)}")
            # 添加异常记录
            error_stats = {'status': 'error', 'message': str(e)}
            history_manager.add_sign_record(self.username, error_stats)
            return False
        finally:
            # 计算总耗时
            total_time = time.time() - start_time
            logger.info(f"[{self.username}] 签到任务结束，总耗时: {total_time:.2f}秒")
