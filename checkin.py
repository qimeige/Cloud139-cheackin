import requests
import json
import os
from datetime import datetime

# 配置信息（从环境变量获取，安全起见不硬编码）
USERNAME = os.environ.get("YD_USERNAME")  # 移动云盘手机号
PASSWORD = os.environ.get("YD_PASSWORD")  # 移动云盘密码
SCKEY = os.environ.get("SCKEY")  # Server酱密钥（用于微信推送，可选）

# 登录接口
LOGIN_URL = "https://cloud.10086.cn/api/login/mobile"
# 签到接口
SIGN_URL = "https://cloud.10086.cn/api/user/signIn"
# 用户信息接口（用于获取昵称）
USER_INFO_URL = "https://cloud.10086.cn/api/user/info"

def send_wechat_msg(title, content):
    """通过Server酱推送消息到微信"""
    if not SCKEY:
        return
    url = f"https://sctapi.ftqq.com/{SCKEY}.send"
    params = {"title": title, "desp": content}
    try:
        requests.get(url, params=params, timeout=10)
    except Exception as e:
        print(f"微信推送失败：{str(e)}")

def login():
    """登录获取Cookie"""
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
        "Content-Type": "application/json"
    }
    data = {
        "mobile": USERNAME,
        "password": PASSWORD,
        "loginType": "0"
    }
    try:
        response = requests.post(
            LOGIN_URL,
            headers=headers,
            data=json.dumps(data),
            timeout=10
        )
        result = response.json()
        if result.get("code") == 200:
            # 提取Cookie（JSESSIONID）
            cookies = response.cookies.get_dict()
            return cookies.get("JSESSIONID")
        else:
            msg = f"登录失败：{result.get('msg', '未知错误')}"
            send_wechat_msg("移动云盘签到失败", msg)
            raise Exception(msg)
    except Exception as e:
        send_wechat_msg("移动云盘签到失败", f"登录请求异常：{str(e)}")
        raise

def get_nickname(cookie):
    """获取用户昵称"""
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
        "Cookie": f"JSESSIONID={cookie}"
    }
    try:
        response = requests.get(USER_INFO_URL, headers=headers, timeout=10)
        result = response.json()
        if result.get("code") == 200:
            return result.get("data", {}).get("nickName", "未知用户")
        return "未知用户"
    except:
        return "未知用户"

def sign_in(cookie):
    """执行签到"""
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
        "Cookie": f"JSESSIONID={cookie}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(
            SIGN_URL,
            headers=headers,
            data=json.dumps({}),
            timeout=10
        )
        result = response.json()
        return result
    except Exception as e:
        send_wechat_msg("移动云盘签到失败", f"签到请求异常：{str(e)}")
        raise

def main():
    if not USERNAME or not PASSWORD:
        raise Exception("请配置账号密码环境变量")
    
    # 登录获取Cookie
    cookie = login()
    # 获取昵称
    nickname = get_nickname(cookie)
    # 执行签到
    sign_result = sign_in(cookie)
    
    # 处理签到结果
    today = datetime.now().strftime("%Y-%m-%d")
    if sign_result.get("code") == 200:
        data = sign_result.get("data", {})
        if data.get("isSign"):
            msg = f"{today} {nickname} 签到成功！\n获得空间：{data.get('space', '0')}MB\n连续签到：{data.get('continuousDays', 0)}天"
        else:
            msg = f"{today} {nickname} 今日已签到"
    else:
        msg = f"{today} {nickname} 签到失败：{sign_result.get('msg', '未知错误')}"
    
    print(msg)
    send_wechat_msg("移动云盘签到结果", msg)

if __name__ == "__main__":
    main()
