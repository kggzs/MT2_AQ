# MT2_AQ MT论坛自动签到系统

这是一个用于MT论坛(bbs.binmt.cc)的自动签到系统，支持多账号管理、验证码自动识别、签到历史记录等功能。

作者：康哥
官网：[www.kggzs.cn](https://www.kggzs.cn)

## 功能特性

- 多账号管理和自动签到
- 百度OCR API自动识别验证码
- 支持安全提问设置
- 智能延迟和重试机制
- 详细的日志记录
- 签到历史和积分统计
- Cookie持久化存储

## 项目结构

```
.
├── README.md           # 项目说明文档
├── accounts.json       # 账号配置文件
├── config.json        # 系统配置文件
├── cookies/           # Cookie存储目录
├── logs/              # 日志文件目录
├── main.py           # 主程序入口
├── modules/          # 功能模块目录
│   ├── __init__.py
│   ├── account_manager.py   # 账号管理模块
│   ├── config_manager.py    # 配置管理模块
│   ├── history_manager.py   # 历史记录管理模块
│   ├── logger.py           # 日志管理模块
│   ├── ocr.py             # 验证码识别模块
│   └── signer.py          # 签到核心模块
└── sign_history.json  # 签到历史记录文件
```

## 功能模块说明

- **account_manager.py**: 负责账号信息的加载、验证和管理
- **config_manager.py**: 处理系统配置的加载和管理
- **history_manager.py**: 管理签到历史记录的保存和统计
- **logger.py**: 提供统一的日志记录功能
- **ocr.py**: 集成百度OCR API进行验证码识别
- **signer.py**: 实现论坛登录和签到的核心功能

## 安装说明

1. 确保已安装Python 3.6或更高版本
2. 安装所需依赖包：
```bash
pip install requests beautifulsoup4 baidu-aip pillow
```
或使用命令安装所有依赖
```bash
pip install -r requirements.txt
```

## 配置说明

### 1. 账号配置
在`accounts.json`文件中配置账号信息：
```json
[
    {
        "username": "你的用户名",
        "password": "你的密码",
        "questionid": 0,  // 安全提问ID，默认为0
        "answer": ""     // 安全提问答案，默认为空
    }
]
```

安全提问ID对照表：

| ID | 安全提问类型 |
|----|-------------|
| 0 | 安全提问(未设置请忽略) |
| 1 | 母亲的名字 |
| 2 | 爷爷的名字 |
| 3 | 父亲出生的城市 |
| 4 | 您其中一位老师的名字 |
| 5 | 您个人计算机的型号 |
| 6 | 您最喜欢的餐馆名称 |
| 7 | 驾驶执照最后四位数字 |

### 2. 验证码识别配置
在`config.json`文件中配置百度OCR API信息：
```json
{
    "API_KEY": "你的百度OCR API Key",
    "SECRET_KEY": "你的百度OCR Secret Key"
}
```

### 3. 其他配置项
可在`config.json`中调整以下参数：
- 账号间隔延迟时间
- 错误重试次数和延迟
- 请求超时设置
- 日志配置选项

## 使用方法

1. 运行程序：
```bash
python main.py
```

2. 程序会自动：
   - 加载配置的账号信息
   - 依次执行每个账号的签到
   - 处理验证码识别
   - 记录签到结果和积分奖励

## 日志和历史记录

- 日志文件保存在`logs`目录下，按日期命名
- 签到历史记录保存在`sign_history.json`文件中
- Cookie文件保存在`cookies`目录下，按用户名命名

## 注意事项

1. 首次使用需要配置账号信息和百度OCR API
2. 建议适当调整账号间隔时间，避免触发网站反爬机制
3. 如遇到签到失败，可查看日志文件了解具体原因
4. 定期检查Cookie有效性，必要时重新登录

## 常见问题

1. 验证码识别失败
   - 检查百度OCR API配置是否正确
   - 确认API额度是否充足
   - 尝试增加验证码识别重试次数

2. 签到失败
   - 检查账号密码是否正确
   - 确认安全提问设置
   - 查看详细错误日志
   - 检查网络连接状态

3. Cookie失效
   - 系统会自动重新登录
   - 可手动删除cookies目录下的对应文件
   - 检查账号是否被封禁或需要手动验证

## 开源许可证

本项目采用 GNU通用公共许可证第3版 (GNU General Public License v3.0)。这意味着：

- 你可以自由地使用、复制、分发和修改本软件
- 如果你修改了本软件，必须以相同的许可证（GPLv3）发布
- 如果你分发本软件，必须开放源代码并提供相同的权利给其他用户
- 必须保留原作者的版权声明和许可证声明
- 对本软件的任何修改都必须明确标注

```
                    GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007

 Copyright (c) 2024 康哥 <www.kggzs.cn>

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <https://www.gnu.org/licenses/>.

                     Additional Permissions

 If you modify this program, you must prominently state in your modified
 version that you have modified it, giving a relevant date and reference
 to the original version.
```
