# -*- coding: utf-8 -*-
'''
夸克自动签到 - GitHub Actions 版本
Author: Adapted from BNDou
Date: 2024-03-15
'''

import os
import re
import sys
import requests

def send(title, message):
    """简单的通知函数，输出到GitHub Actions日志"""
    print(f"【{title}】\n{message}")
    return True

def get_env():
    """获取环境变量"""
    if "COOKIE_QUARK" in os.environ:
        cookie_list = re.split('\n|&&', os.environ.get('COOKIE_QUARK'))
    else:
        print('❌未添加COOKIE_QUARK变量')
        send('夸克自动签到', '❌未添加COOKIE_QUARK变量')
        sys.exit(0)
    return cookie_list

class Quark:
    def __init__(self, user_data):
        self.param = user_data

    def convert_bytes(self, b):
        units = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = 0
        while b >= 1024 and i < len(units) - 1:
            b /= 1024
            i += 1
        return f"{b:.2f} {units[i]}"

    def get_growth_info(self):
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/info"
        querystring = {
            "pr": "ucpro",
            "fr": "android",
            "kps": self.param.get('kps'),
            "sign": self.param.get('sign'),
            "vcode": self.param.get('vcode')
        }
        response = requests.get(url=url, params=querystring).json()
        if response.get("data"):
            return response["data"]
        else:
            return False

    def get_growth_sign(self):
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/sign"
        querystring = {
            "pr": "ucpro",
            "fr": "android",
            "kps": self.param.get('kps'),
            "sign": self.param.get('sign'),
            "vcode": self.param.get('vcode')
        }
        data = {"sign_cyclic": True}
        response = requests.post(url=url, json=data, params=querystring).json()
        if response.get("data"):
            return True, response["data"]["sign_daily_reward"]
        else:
            return False, response.get("message", "签到失败")

    def do_sign(self):
        log = ""
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
        return log

def extract_params(url):
    query_start = url.find('?')
    query_string = url[query_start + 1:] if query_start != -1 else ''
    params = {}
    for param in query_string.split('&'):
        if '=' in param:
            key, value = param.split('=', 1)
            params[key] = value
    return {
        'kps': params.get('kps', ''),
        'sign': params.get('sign', ''),
        'vcode': params.get('vcode', '')
    }

def main():
    msg = "夸克签到结果：\n\n"
    cookie_quark = get_env()
    print("✅ 检测到共", len(cookie_quark), "个夸克账号\n")

    for i, cookie in enumerate(cookie_quark):
        user_data = {}
        for item in cookie.replace(" ", "").split(';'):
            if item and '=' in item:
                key, value = item.split('=', 1)
                user_data[key] = value
        
        if 'url' in user_data:
            url_params = extract_params(user_data['url'])
            user_data.update(url_params)
        
        msg += f"🙍🏻‍♂️ 第{i + 1}个账号"
        log = Quark(user_data).do_sign()
        msg += log + "\n"

    send('夸克自动签到', msg)
    return msg

if __name__ == "__main__":
    print("----------夸克网盘开始签到----------")
    main()
    print("----------夸克网盘签到完毕----------")
