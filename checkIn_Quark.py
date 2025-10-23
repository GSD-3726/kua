# -*- coding: utf-8 -*-
'''
夸克自动签到 - 调试版本
'''

import os
import re
import sys
import requests
import json

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

class Quark:
    def __init__(self, user_data):
        self.param = user_data
        self.session = requests.Session()
        # 添加移动端请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'Origin': 'https://drive-m.quark.cn',
            'Referer': 'https://drive-m.quark.cn/'
        })

    def convert_bytes(self, b):
        units = ("B", "KB", "MB", "GB", "TB")
        i = 0
        while b >= 1024 and i < len(units) - 1:
            b /= 1024
            i += 1
        return f"{b:.2f} {units[i]}"

    def debug_request(self, url, params, method='GET', data=None):
        """调试请求函数"""
        print(f"\n🔍 请求调试信息:")
        print(f"URL: {url}")
        print(f"方法: {method}")
        print(f"参数: { {k: '***' if k in ['kps','sign','vcode'] else v for k, v in params.items()} }")
        
        try:
            if method == 'GET':
                response = self.session.get(url, params=params, timeout=10)
            else:
                response = self.session.post(url, params=params, json=data, timeout=10)
            
            print(f"状态码: {response.status_code}")
            print(f"响应内容: {response.text[:500]}...")  # 只显示前500字符
            
            return response
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return None

    def get_growth_info(self):
        """获取用户当前的签到信息"""
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/info"
        querystring = {
            "pr": "ucpro",
            "fr": "android",
            "kps": self.param.get('kps'),
            "sign": self.param.get('sign'),
            "vcode": self.param.get('vcode')
        }
        
        print(f"\n📊 尝试获取成长信息...")
        print(f"账号: {self.param.get('user', '未知用户')}")
        print(f"参数状态: kps={'有' if self.param.get('kps') else '无'}, "
              f"sign={'有' if self.param.get('sign') else '无'}, "
              f"vcode={'有' if self.param.get('vcode') else '无'}")
        
        response = self.debug_request(url, querystring, 'GET')
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if data.get("data"):
                    print("✅ 成功获取成长信息")
                    return data["data"]
                else:
                    print(f"❌ 响应中无data字段: {data.get('message', '未知错误')}")
                    return False
            except Exception as e:
                print(f"❌ JSON解析失败: {e}")
                return False
        else:
            print("❌ 请求失败或状态码异常")
            return False

    def get_growth_sign(self):
        """执行签到"""
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/sign"
        querystring = {
            "pr": "ucpro",
            "fr": "android", 
            "kps": self.param.get('kps'),
            "sign": self.param.get('sign'),
            "vcode": self.param.get('vcode')
        }
        data = {"sign_cyclic": True}
        
        print(f"\n🎯 尝试执行签到...")
        response = self.debug_request(url, querystring, 'POST', data)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if data.get("data"):
                    return True, data["data"]["sign_daily_reward"]
                else:
                    return False, data.get("message", "签到失败")
            except Exception as e:
                return False, f"JSON解析失败: {e}"
        else:
            return False, "请求失败"

    def do_sign(self):
        """执行签到任务"""
        log = ""
        print(f"\n{'='*50}")
        print(f"开始处理账号: {self.param.get('user', '未知用户')}")
        
        growth_info = self.get_growth_info()
        if growth_info:
            user_type = '88VIP' if growth_info.get('88VIP') else '普通用户'
            log += f" {user_type} {self.param.get('user', '未知用户')}\n"
            log += f"💾 网盘总容量：{self.convert_bytes(growth_info['total_capacity'])}，"
            
            sign_reward = growth_info['cap_composition'].get('sign_reward', 0)
            log += f"签到累计容量：{self.convert_bytes(sign_reward)}\n"
            
            if growth_info["cap_sign"]["sign_daily"]:
                log += f"✅ 今日已签到+{self.convert_bytes(growth_info['cap_sign']['sign_daily_reward'])}，"
                log += f"连签进度({growth_info['cap_sign']['sign_progress']}/{growth_info['cap_sign']['sign_target']})\n"
            else:
                sign, sign_return = self.get_growth_sign()
                if sign:
                    log += f"✅ 执行签到: 今日签到+{self.convert_bytes(sign_return)}，"
                    log += f"连签进度({growth_info['cap_sign']['sign_progress'] + 1}/{growth_info['cap_sign']['sign_target']})\n"
                else:
                    log += f"❌ 签到异常: {sign_return}\n"
        else:
            log += f"❌ 签到异常: 获取成长信息失败\n"
        
        print(f"处理完成: {log}")
        return log

def extract_params(url):
    """从URL中提取参数"""
    if not url:
        return {}
        
    query_start = url.find('?')
    if query_start == -1:
        print("❌ URL中未找到参数部分")
        return {}
        
    query_string = url[query_start + 1:]
    params = {}
    
    for param in query_string.split('&'):
        if '=' in param:
            key, value = param.split('=', 1)
            params[key] = value
    
    print(f"🔧 从URL提取参数: {list(params.keys())}")
    return params

def main():
    """主函数"""
    msg = "夸克签到结果：\n\n"
    cookie_quark = get_env()

    for i, cookie in enumerate(cookie_quark):
        user_data = {}
        print(f"\n{'='*50}")
        print(f"解析第 {i+1} 个账号配置...")
        
        # 解析cookie字符串
        for item in cookie.replace(" ", "").split(';'):
            if item and '=' in item:
                key, value = item.split('=', 1)
                user_data[key] = value
                if key in ['user', 'url']:
                    print(f"  {key}: {value[:50]}...")
        
        # 从URL中提取参数
        if 'url' in user_data:
            url_params = extract_params(user_data['url'])
            user_data.update(url_params)
        else:
            print("❌ 配置中未找到url参数")
        
        # 检查必要参数
        required_params = ['kps', 'sign', 'vcode']
        missing_params = [p for p in required_params if not user_data.get(p)]
        if missing_params:
            print(f"❌ 缺少必要参数: {missing_params}")
            msg += f"🙍🏻‍♂️ 第{i+1}个账号 - 缺少参数: {missing_params}\n"
            continue
        
        msg += f"🙍🏻‍♂️ 第{i+1}个账号"
        log = Quark(user_data).do_sign()
        msg += log + "\n"

    send('夸克自动签到', msg)
    return msg

if __name__ == "__main__":
    print("----------夸克网盘开始签到----------")
    main()
    print("----------夸克网盘签到完毕----------")
