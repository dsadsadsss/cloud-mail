#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
域名邮箱API客户端
使用API接口获取邮件列表
"""

# =====================================================================
#                           导入依赖
# =====================================================================

import requests
import json
import datetime
from typing import Optional, Dict, List, Any

# =====================================================================
#                          配置区域
# =====================================================================

# 邮箱API配置
API_BASE_URL = "https://mail.faiz.us.kg"  # API地址——邮箱网址
EMAIL = ""  # 接码邮箱
PASSWORD = ""  # 邮箱密码
JWT_SECRET = ""  # JWT秘钥（用于生成token）

# 邮件查询条件（用于获取指定邮件）
TO_EMAIL = ""  # 收件人邮箱（留空则使用登录邮箱，可指定子邮箱）
SEND_EMAIL = "account@nvidia.com"  # 发件人邮箱（可选，留空则不过滤）
SUBJECT = "验证您的电子邮箱地址"  # 邮件主题（可选，留空则不过滤）
LOCAL_FILTER = True  # 是否使用本地过滤（当主题包含特殊字符时建议开启，一般是俄文、日文、德文等）

# =====================================================================
#                        邮箱API客户端类
# =====================================================================

class EmailAPI:
    """域名邮箱API客户端 - 提供邮件查询功能"""
    
    def __init__(self, base_url: str = None):
        """初始化邮箱API客户端"""
        self.base_url = (base_url or API_BASE_URL).rstrip('/')
        self.token = None
    
    # =================================================================
    #                       1. Token获取模块
    # =================================================================
    
    def get_token(self, email: str, password: str, jwt_secret: str = JWT_SECRET) -> Dict[str, Any]:
        """生成Token"""
        url = f"{self.base_url}/api/public/genToken"
        headers = {"Authorization": jwt_secret}
        payload = {"email": email, "password": password}
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            data = response.json()
            
            if data.get("code") == 200:
                self.token = data.get("data", {}).get("token")
            
            return data
        except Exception as e:
            return {"code": -1, "message": str(e)}
    
    # =================================================================
    #                       2. 邮件查询模块
    # =================================================================
    
    def get_mail_list(
        self,
        hd_email: str,
        send_name: Optional[str] = None,
        send_email: Optional[str] = None,
        subject: Optional[str] = None,
        content: Optional[str] = None,
        send_sort: str = "desc",
        mail_type: int = 0,
        num: int = 1,
        size: int = 20
    ) -> Dict[str, Any]:
        """查询邮件列表"""
        # 检查token
        if not self.token:
            return {"code": -1, "message": "请先调用 get_token() 生成token"}
        
        # 根据API文档，正确的接口是 /api/public/emailList （注意L是大写）
        url = f"{self.base_url}/api/public/emailList"
        headers = {
            "Authorization": self.token
        }
        
        # 构建请求参数（必填参数）
        payload = {
            "toEmail": hd_email,      # 收件人邮箱
            "timeSort": send_sort,     # 时间排序
            "type": mail_type,         # 邮件类型
            "num": num,                # 页码
            "size": min(size, 20)      # 每页数量（最大20）
        }
        
        # 添加可选参数（只添加非空参数）
        if send_name:
            payload["sendName"] = send_name
        if send_email:
            payload["sendEmail"] = send_email
        if subject:
            payload["subject"] = subject
        if content:
            payload["content"] = content
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            return {"code": -1, "message": str(e)}

# =====================================================================
#                          辅助函数
# =====================================================================

def save_emails_to_json(mail_list: List[Dict], filename: str = None) -> str:
    """保存邮件到JSON文件"""
    if filename is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"emails_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(mail_list, f, ensure_ascii=False, indent=2)
    
    return filename

# =====================================================================
#                          测试与示例
# =====================================================================

def test_mail_functions(save_to_file: bool = True, debug_mode: bool = False):
    """测试邮件功能"""
    # ========== 步骤1：初始化并获取Token ==========
    api = EmailAPI(base_url=API_BASE_URL)
    token_result = api.get_token(EMAIL, PASSWORD, JWT_SECRET)
    
    if token_result.get("code") != 200:
        print(f"\n[失败] Token获取失败: {token_result.get('message')}")
        return
    
    print(f"[成功] Token获取成功")
    
    # ========== 步骤2：确定收件人邮箱 ==========
    target_email = TO_EMAIL if TO_EMAIL else EMAIL
    
    # ========== 步骤3：查询邮件 ==========
    if LOCAL_FILTER and SUBJECT:
        # 使用本地过滤
        mail_result = api.get_mail_list(
            hd_email=target_email,
            send_email=SEND_EMAIL if SEND_EMAIL else None,
            send_sort="desc",
            num=1,
            size=20
        )
    else:
        # 直接API查询
        mail_result = api.get_mail_list(
            hd_email=target_email,
            send_email=SEND_EMAIL if SEND_EMAIL else None,
            subject=SUBJECT if SUBJECT else None,
            send_sort="desc",
            num=1,
            size=10
        )
    
    # ========== 步骤3：处理结果 ==========
    if mail_result.get("code") == 200:
        # 提取邮件列表
        data_content = mail_result.get("data", [])
        mail_list = data_content if isinstance(data_content, list) else data_content.get("list", [])
        
        # 本地过滤主题
        if LOCAL_FILTER and SUBJECT and mail_list:
            mail_list = [mail for mail in mail_list if SUBJECT.lower() in mail.get('subject', '').lower()]
        
        if mail_list:
            # 只保留最新的一封邮件
            latest_mail = [mail_list[0]]
            print(f"[成功] 查询成功，获取最新邮件")
            
            # 保存到JSON文件
            if save_to_file:
                filename = save_emails_to_json(latest_mail)
                print(f"[成功] 邮件已保存: {filename}")
        else:
            print(f"[信息] 未找到符合条件的邮件")
    else:
        print(f"[失败] 查询失败: {mail_result.get('message')}")

# =====================================================================
#                          主程序入口
# =====================================================================

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("域名邮箱API - 邮件查询")
    print("=" * 60)
    
    # 显示API配置
    print(f"\nAPI配置:")
    print(f"  API地址: {API_BASE_URL}")
    print(f"  邮箱地址: {EMAIL}")
    print(f"  密码: {PASSWORD[:4]}{'*' * (len(PASSWORD) - 4)}")
    print(f"  JWT秘钥: {JWT_SECRET[:8]}{'*' * (len(JWT_SECRET) - 8)}")
    
    # 显示查询条件
    print(f"\n查询条件:")
    print(f"  收件人: {TO_EMAIL if TO_EMAIL else EMAIL + ' (默认)'}")
    if SEND_EMAIL:
        print(f"  发件人: {SEND_EMAIL}")
    if SUBJECT:
        print(f"  主题: {SUBJECT}")
    print()
    
    # 运行查询
    test_mail_functions(debug_mode=False)
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
