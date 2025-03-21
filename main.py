# -*- coding: utf-8 -*-
import os
import time
import random
from datetime import datetime

# 导入自定义模块
from modules.logger import logger
from modules.config_manager import config_manager
from modules.account_manager import account_manager
from modules.history_manager import history_manager
from modules.signer import DzSigner

def run_multi_sign():
    """执行多账号签到"""
    # 加载账号信息
    accounts = account_manager.get_accounts()
    if not accounts:
        logger.warning("没有可用的账号信息，请检查账号配置文件")
        return False
        
    current_date = datetime.now().strftime("%Y-%m-%d")
    logger.info(f"===== 开始执行MT论坛多账号自动签到 - {current_date} =====")
    
    # 获取延迟配置
    account_delay_min = config_manager.get('sign', 'account_delay', {}).get('min', 5)
    account_delay_max = config_manager.get('sign', 'account_delay', {}).get('max', 10)
    error_delay_min = config_manager.get('sign', 'error_delay', {}).get('min', 10)
    error_delay_max = config_manager.get('sign', 'error_delay', {}).get('max', 15)
    
    success_count = 0
    fail_count = 0
    total_rewards = 0
    start_time = time.time()
    
    # 循环执行每个账号的签到
    for i, account in enumerate(accounts):
        try:
            username = account.get('username')
            password = account.get('password')
            questionid = account.get('questionid', 0)  # 获取安全提问ID，默认为0
            answer = account.get('answer', "")  # 获取安全提问答案，默认为空
            
            if not username or not password:
                logger.error(f"账号信息不完整，跳过: {account}")
                fail_count += 1
                continue
                
            logger.info(f"正在处理第 {i+1}/{len(accounts)} 个账号: {username}")
            
            # 创建签到实例并执行
            signer = DzSigner(username, password, questionid, answer)
            result = signer.run()
            
            success_count += 1 if result else fail_count + 1
            
            # 获取账号历史记录，提取积分奖励
            account_history = history_manager.get_account_history(username)
            if result and account_history and account_history['history']:
                latest_record = account_history['history'][-1]
                total_rewards += latest_record.get('reward', 0)
            
            # 非最后一个账号需要添加随机延迟
            if i < len(accounts) - 1:
                delay = random.uniform(account_delay_min, account_delay_max)
                logger.info(f"等待 {delay:.2f} 秒后处理下一个账号...")
                time.sleep(delay)
                
        except Exception as e:
            account_username = account['username'] if isinstance(account, dict) and 'username' in account else '未知'
            logger.error(f"处理账号 {account_username} 时出现未捕获的异常: {str(e)}")
            fail_count += 1
            
            # 非最后一个账号出现异常时添加额外延迟
            if i < len(accounts) - 1:
                delay = random.uniform(error_delay_min, error_delay_max)
                logger.info(f"出现异常，等待 {delay:.2f} 秒后继续...")
                time.sleep(delay)
    
    # 计算总耗时
    total_time = time.time() - start_time
    
    # 输出签到统计信息
    logger.info(f"===== MT论坛多账号签到完成 - {current_date} =====")
    logger.info(f"总账号数: {len(accounts)}")
    logger.info(f"成功签到: {success_count}")
    logger.info(f"签到失败: {fail_count}")
    logger.info(f"总积分奖励: {total_rewards}")
    logger.info(f"总耗时: {total_time:.2f}秒")
    
    # 添加每日汇总到历史记录
    summary_data = {
        "total_accounts": len(accounts),
        "success_count": success_count,
        "fail_count": fail_count,
        "total_rewards": total_rewards,
        "execution_time": round(total_time, 2)
    }
    history_manager.add_daily_summary(summary_data)
    
    return success_count > 0  # 返回是否至少有一个账号签到成功

if __name__ == '__main__':
    run_multi_sign()
