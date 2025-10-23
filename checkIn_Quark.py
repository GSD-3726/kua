# -*- coding: utf-8 -*-
'''
夸克自动签到 - 修复参数解析版本
'''

import os
import re
import sys
import requests
from urllib.parse import urlparse, parse_qs

def send(title, message):
    """简单的通知函数"""
    print(f"【{title}】\n{message}")
    return True

def get_env():
    """获取环境变量"""
    if "COOKIE_QUARK" in os.environ:
        cookie_list = re.split('\n|&&', os.environ.get('COOKIE_QUARK'))
        print(f"✅ 成功读取环境变量，共 {len(cookie_list)} 个账号")
        return cookie_list
    else:
        print('❌ 未添加COOKIE_QUARK变量')
        send('夸克自动签到', '❌未添加COOKIE_QUARK变量')
        sys.exit(0)

def extract_params(url):
    """从URL中提取所需的参数 - 修复版本"""
    if not url:
        print("❌ URL为空")
        return {}
    
    print(f"🔧 解析URL，长度: {len(url)}")
    
    try:
        # 使用urllib解析URL
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        params = {}
        required_params = ['kps', 'sign', 'vcode']
        
        for key in required_params:
            if key in query_params and query_params[key]:
                params[key] = query_params[key][0]
                print(f"✅ 提取 {key}: 长度{len(params[key])}")
            else:
                print(f"❌ 未找到参数: {key}")
        
        return params
        
    except Exception as e:
        print(f"❌ URL解析异常: {e}")
        # 尝试备用方法：正则表达式
        return extract_params_fallback(url)

def extract_params_fallback(url):
    """备用参数提取方法"""
    print("🔄 使用备用方法提取参数")
    params = {}
    
    try:
        # 使用正则表达式提取
        kps_match = re.search(r'kps=([^&]+)', url)
        sign_match = re.search(r'sign=([^&]+)', url)
        vcode_match = re.search(r'vcode=([^&]+)', url)
        
        if kps_match:
            params['kps'] = kps_match.group(1)
            print(f"✅ 备用方法提取kps: 长度{len(params['kps'])}")
        if sign_match:
            params['sign'] = sign_match.group(1)
            print(f"✅ 备用方法提取sign: 长度{len(params['sign'])}")
        if vcode_match:
            params['vcode'] = vcode_match.group(1)
            print(f"✅ 备用方法提取vcode: {params['vcode']}")
            
    except Exception as e:
        print(f"❌ 备用方法也失败: {e}")
    
    return params

class Quark:
    def __init__(self, user_data):
        self.param = user_data
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
        })

    def convert_bytes(self, b):
        units = ("B", "KB", "MB", "GB", "TB")
        i = 0
        while b >= 1024 and i < len(units) - 1:
            b /= 1024
            i += 1
        return f"{b:.2f} {units[i]}"

    def get_growth_info(self):
        """获取成长信息"""
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/info"
        querystring = {
            "pr": "ucpro",
            "fr": "android",
            "kps": self.param.get('kps'),
            "sign": self.param.get('sign'),
            "vcode": self.param.get('vcode')
        }
        
        print("📊 获取成长信息...")
        try:
            response = self.session.get(url, params=querystring, timeout=10)
            print(f"📡 请求状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    print("✅ 成功获取成长信息")
                    return data["data"]
                else:
                    print(f"❌ API返回异常: {data.get('message', '未知错误')}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            
        return False

    def do_sign(self):
        """执行签到任务"""
        log = ""
        print(f"\n{'='*50}")
        print("开始处理账号...")
        
        # 检查必要参数
        required_params = ['kps', 'sign', 'vcode']
        missing_params = [p for p in required_params if not self.param.get(p)]
        
        if missing_params:
            log = f"❌ 缺少参数: {missing_params}\n"
            log += f"当前参数: {list(self.param.keys())}"
            print(log)
            return log

        growth_info = self.get_growth_info()
        if growth_info:
            user_type = '88VIP' if growth_info.get('88VIP') else '普通用户'
            log += f" {user_type} {self.param.get('user', '未知用户')}\n"
            log += f"💾 网盘总容量：{self.convert_bytes(growth_info['total_capacity'])}\n"
            
            if growth_info["cap_sign"]["sign_daily"]:
                log += f"✅ 今日已签到\n"
            else:
                log += f"🔄 今日未签到，需要执行签到操作\n"
        else:
            log += f"❌ 获取成长信息失败\n"

        return log

def main():
    """主函数"""
    msg = "夸克签到结果：\n\n"
    cookie_quark = get_env()

    for i, cookie in enumerate(cookie_quark):
        print(f"\n📝 处理第 {i + 1} 个账号")
        
        # 解析用户数据
        user_data = {}
        for item in cookie.replace(" ", "").split(';'):
            if item and '=' in item:
                key, value = item.split('=', 1)
                user_data[key] = value
                print(f"   {key}: {value[:50]}{'...' if len(value) > 50 else ''}")

        # 从URL中提取参数
        if 'url' in user_data:
            print("🔗 从URL提取参数...")
            url_params = extract_params(user_data['url'])
            user_data.update(url_params)
        else:
            print("❌ 配置中未找到url参数")

        # 检查必要参数
        required_params = ['kps', 'sign', 'vcode']
        missing_params = [p for p in required_params if not user_data.get(p)]
        
        if missing_params:
            msg += f"🙍🏻‍♂️ 第{i + 1}个账号 - 缺少参数: {missing_params}\n"
            continue

        msg += f"🙍🏻‍♂️ 第{i + 1}个账号"
        log = Quark(user_data).do_sign()
        msg += log + "\n"

    send('夸克自动签到', msg)
    return msg

if __name__ == "__main__":
    print("----------夸克网盘开始签到----------")
    main()
    print("----------夸克网盘签到完毕----------")
