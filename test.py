import configparser
import sys
import json
import requests
import os
import time
import base64
import random
from datetime import datetime, timedelta
import execjs
from Crypto.Cipher import PKCS1_v1_5
import traceback
import binascii
from Crypto.PublicKey import RSA
from requests.exceptions import RequestException, Timeout
from bs4 import BeautifulSoup
from requests_toolbelt.multipart.encoder import MultipartEncoder
from urllib.parse import quote
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pksc1_v1_5
# ====================== 场地 URL 定义 ======================
url1 = "https://elife.fudan.edu.cn/public/front/toResourceFrame.htm?contentId=8aecc6ce90ae440c0191458edad81857"  # 江湾室内网球场
url2 = "https://elife.fudan.edu.cn/public/front/toResourceFrame.htm?contentId=8aecc6ce780fe18301786c51f2a5627b"  # 江湾室外网球场
url3 = "https://elife.fudan.edu.cn/public/front/toResourceFrame.htm?contentId=8aecc6ce6b6e6698016bc5dc173c11b7"  # 南区网球场
url4 = "https://elife.fudan.edu.cn/public/front/toResourceFrame.htm?contentId=8aecc6ce749544fd01749a31a04332c2"  # 江湾室内羽毛球场
url5 = "https://elife.fudan.edu.cn/public/front/toResourceFrame.htm?contentId=2c9c486e4f821a19014f826f2a4f0036"  # 北区羽毛球场
url6 = "https://elife.fudan.edu.cn/public/front/toResourceFrame.htm?contentId=8aecc6ce8ee75f34018f047dc8ca407a"  # 张江网球场
url7 = "https://elife.fudan.edu.cn/public/front/toResourceFrame.htm?contentId=8aecc6ce878581d701879c7548c6737d"  # 江湾排球场1号
url8 = "https://elife.fudan.edu.cn/public/front/toResourceFrame.htm?contentId=8aecc6ce7d2dffbd017de9ea4e7e4ece"  # 国权路
url9 = "https://elife.fudan.edu.cn/public/front/toResourceFrame.htm?contentId=2c9c486e4f821a19014f827298da0047"  # 北区排球场
url10 = "https://elife.fudan.edu.cn/public/front/toResourceFrame.htm?contentId=2c9c486e4f821a19014f82418a900004"  # 正大羽毛球
url11 = "https://elife.fudan.edu.cn/public/front/toResourceFrame.htm?contentId=8aecc6ce7176eb18017225c2e7d62831"  # 江湾排球场2号
# ====================== 业务可配置区（只改这里就行） ======================
config = configparser.ConfigParser()
config.read('config1.ini')
TARGET_URL = url4          # 想预约的场地（默认：江湾排球场1号）
TIMES = [9,8]          # 想抢的时间段
DAY_OFFSET = 2             # 预约几天后：0=今天，1=明天，2=后天

TRIGGER_HOUR = 6           # 抢场开始执行脚本的时间（小时）
TRIGGER_MINUTE = 59        # 分钟
TRIGGER_SECOND = 59        # 秒
# ====================== 其他基础配置 ======================
username = config.get('credentials', 'username')
password = config.get('credentials', 'password')
mobile = config.get('credentials', 'phone')

refresh_count = 4
refresh_time = 4
refresh_time2 = 8

# ====================== RSA 公钥（登录加密用） ======================
pem_key = """-----BEGIN PUBLIC KEY-----
       MIIBojANBgkqhkiG9w0BAQEFAAOCAY8AMIIBigKCAYEAhKhGYdd8cnjFtpZ4nZj2CPKVZUa6gJG8lZoCz4mspFjOyZxS4iOFzEV9B4iIu5TTlwwSfAmtD1k+nT5CgYDF9oihTCzuCHoq9LTiTftKUohZUq+2nVjOLI25u6/D0p5Kp467KjB72hfgCVyUhkVXgVWtI44bgmGFGUIVOKzMYW29d++JC5Tcn/B/oMwyuTG+pFSrN3UYdjvvPzZiEiwCfD+ONJiQC5Bnmk9yiimSk0cs9UcKUttPoKrjIYx9P3l+fE7Jh4PRKJ/3J5VccJXdidRTblq/wimtLJpJLS8atLlDmxon7tGQq68O+n7JRe8MtIOWv1oFEzNatETZFi2Ms3gGGzMDMhUwfWwh0m7gu25nrAEFjSssLkNz0B6YFC1GeK69Sy2jgbGPVxKkXzjK9kv328hUmg3TbwiEydIdSmx6vh4fCr2A7aOWaEvhT2vn4108KlGR+lL9m49OkhFIO6AlZGC/COOdbxhbNCY1X3JX6kTdj8+mflRhJWcpbd6rAgMBAAE=
       -----END PUBLIC KEY-----"""


def rsa_encrypt(message, pem_public_key):
    """极简RSA加密函数：明文 -> 十六进制密文字符串"""
    public_key = RSA.import_key(pem_public_key)
    cipher = PKCS1_v1_5.new(public_key)
    encrypted = cipher.encrypt(message.encode('utf-8'))
    hex_result = binascii.hexlify(encrypted).decode('ascii')
    return hex_result if len(hex_result) % 2 == 0 else '0' + hex_result


class FD:
    def __init__(self, loginName, password, url):
        self.loginName = str(loginName)
        self.password = str(password)
        self.url = url
        self.REQID = ''
        self.lck = ''
        self.authChainCode = ''
        self.loginToken = ''
        self.NSC_Xfc = ''
        self.JSESSIONID = ''
        self.usk = ''
        self.id = []
        self.serviceCategoryId = ''
        self.serviceContentId = ''
        self.currentDate = ''
        # 动态 cookie 名
        self.nsc_cookie_name = None

        self.headers = {
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        }

    def encrypt(self):
        key = '-----BEGIN PUBLIC KEY-----\n' + "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCOrdWTLglhdgMDUIIaDoQI9IWp+S0elwYsy8P5luxbAL5SkohMO4lrwz1Ji0zPCa5nLXZ1CC8xYh6u/TBbdG7YWDqOrj5eR+e3UmDuj0t3j2XZwp+/R7WICydgzu89e4ZtDQly72rtziWGqbCyg7LG5lpvel1ejKJocJgYJE7WxQIDAQAB" + '\n-----END PUBLIC KEY-----'
        string = 'FuDan_' + str(round(time.time() * 1000))
        rsakey = RSA.importKey(key)
        cipher = PKCS1_v1_5.new(rsakey)
        encrypt_text = cipher.encrypt(string.encode())
        cipher_text_tmp = base64.b64encode(encrypt_text)
        return cipher_text_tmp.decode()

    def getLoction0(self):
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        response = requests.get('https://elife.fudan.edu.cn/login2.action',
                                headers=headers,
                                allow_redirects=False)

        print("getLoction0 status:", response.status_code)
        print("getLoction0 cookies:", response.cookies.get_dict())
        print("getLoction0 Set-Cookie:", response.headers.get("Set-Cookie"))

        cookies_dict = response.cookies.get_dict()
        if not cookies_dict:
            raise RuntimeError(
                "未从响应中获取到任何 Cookie，"
                f"Set-Cookie = {response.headers.get('Set-Cookie')}"
            )

        # 取第一个 cookie 作为 NSC_Xfc（当前只返回这一个）
        self.nsc_cookie_name, self.NSC_Xfc = next(iter(cookies_dict.items()))
        print(f"使用动态 Cookie 名: {self.nsc_cookie_name}")

        time.sleep(0.3)
        return response.headers.get("Location")

    def getgetLoction1(self):
        url = self.getLoction0()
        headers = {
            'authority': 'id.fudan.edu.cn',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        }

        response = requests.get(url, headers=headers, allow_redirects=False)
        Location = response.headers.get("Location")
        self.REQID = response.cookies['REQID']
        self.lck = Location.split('lck=')[1].split('&')[0]
        time.sleep(0.3)

    def getauthChainCode(self):
        cookies = {
            'REQID': self.REQID,
        }

        headers = {
            'authority': 'id.fudan.edu.cn',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cache-control': 'no-cache',
            'content-type': 'application/json;charset=UTF-8',
            'origin': 'https://id.fudan.edu.cn',
            'pragma': 'no-cache',
            'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        }

        json_data = {
            'lck': self.lck,
            'entityId': 'https://elife.fudan.edu.cn',
        }

        response = requests.post('https://id.fudan.edu.cn/idp/authn/queryAuthMethods',
                                 cookies=cookies,
                                 headers=headers, json=json_data)
        self.authChainCode = response.json()['data'][0]['authChainCode']
        time.sleep(0.3)

    def login(self):
        cookies = {
            'REQID': self.REQID,
        }

        headers = {
            'authority': 'id.fudan.edu.cn',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cache-control': 'no-cache',
            'content-type': 'application/json;charset=UTF-8',
            'origin': 'https://id.fudan.edu.cn',
            'pragma': 'no-cache',
            'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        }

        json_data = {
            'authModuleCode': 'userAndPwd',
            'authChainCode': self.authChainCode,
            'entityId': 'https://elife.fudan.edu.cn',
            'requestType': 'chain_type',
            'lck': self.lck,
            'authPara': {
                'loginName': self.loginName,
                'password': self.password,
                'verifyCode': '',
            },
        }

        response = requests.post('https://id.fudan.edu.cn/idp/authn/authExecute',
                                 cookies=cookies,
                                 headers=headers, json=json_data)
        self.loginToken = response.json()["loginToken"]
        time.sleep(0.5)

    def login0(self):
        cookies = {
            'REQID': self.REQID,
        }

        headers = {
            'authority': 'id.fudan.edu.cn',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'null',
            'pragma': 'no-cache',
            'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        }

        params = {
            'locale': 'zh-CN',
        }

        data = {
            'loginToken': self.loginToken,
        }

        response = requests.post(
            'https://id.fudan.edu.cn/idp/authCenter/authnEngine',
            params=params,
            cookies=cookies,
            headers=headers,
            data=data,
        )
        nexturl = response.text.split('var locationValue = "')[1].split('";')[0]
        self.usk = response.cookies['usk']
        time.sleep(0.5)
        return nexturl

    def login1(self):
        url = self.login0()
        cookies = {
            self.nsc_cookie_name: self.NSC_Xfc,
        }

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Referer': 'https://id.fudan.edu.cn/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-site',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        response = requests.get(url, cookies=cookies, headers=headers, allow_redirects=False)
        self.JSESSIONID = response.cookies['JSESSIONID']
        nexturl = response.headers.get("Location")
        time.sleep(0.5)
        return nexturl

    def login2(self):
        url = self.login1()
        cookies = {
            self.nsc_cookie_name: self.NSC_Xfc,
            'JSESSIONID': self.JSESSIONID,
        }

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Referer': 'https://id.fudan.edu.cn/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-site',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        response = requests.get(url=url, cookies=cookies,
                                headers=headers, allow_redirects=False)
        nexturl = response.headers.get("Location")
        time.sleep(0.5)
        return nexturl

    def login3(self):
        url = self.login2()
        cookies = {
            'usk': self.usk,
        }

        headers = {
            'authority': 'id.fudan.edu.cn',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'referer': 'https://id.fudan.edu.cn/',
            'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-site',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        }

        response = requests.get(url=url, cookies=cookies, headers=headers,
                                allow_redirects=False)
        nexturl = response.text.split('var locationValue = "')[1].split('"')[0]
        time.sleep(0.5)
        return nexturl

    def login4(self):
        url = self.login3()
        cookies = {
            self.nsc_cookie_name: self.NSC_Xfc,
            'JSESSIONID': self.JSESSIONID,
        }

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Referer': 'https://id.fudan.edu.cn/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-site',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        response = requests.get(url=url, cookies=cookies, headers=headers, allow_redirects=False)
        nexturl = response.headers.get("Location")
        time.sleep(0.5)
        return nexturl

    def login5(self):
        url = self.login4()
        cookies = {
            self.nsc_cookie_name: self.NSC_Xfc,
            'JSESSIONID': self.JSESSIONID,
        }

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Referer': 'https://id.fudan.edu.cn/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-site',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        response = requests.get(url=url, cookies=cookies,
                                headers=headers, allow_redirects=False)
        nexturl = response.headers.get('Location')
        time.sleep(0.5)
        return nexturl

    def login6(self):
        url = self.login5()
        cookies = {
            self.nsc_cookie_name: self.NSC_Xfc,
            'JSESSIONID': self.JSESSIONID,
        }

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Referer': 'https://id.fudan.edu.cn/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-site',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        response = requests.get(url=url,
                                cookies=cookies, headers=headers, allow_redirects=False)
        nexturl = response.headers.get('Location')
        time.sleep(0.5)
        return nexturl

    def login7(self):
        url = self.login6()
        cookies = {
            self.nsc_cookie_name: self.NSC_Xfc,
            'JSESSIONID': self.JSESSIONID,
        }

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Referer': 'https://id.fudan.edu.cn/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-site',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        requests.get(url=url,
                     cookies=cookies, headers=headers)
        time.sleep(0.5)

    def get_tennis_place(self):
        cookies = {
            self.nsc_cookie_name: self.NSC_Xfc,
            'JSESSIONID': self.JSESSIONID,
        }
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        for _ in range(refresh_count):
            try:
                response = requests.get(
                    url=self.url,
                    cookies=cookies,
                    headers=headers,
                    timeout=5,
                )
                soup = BeautifulSoup(response.text, 'html.parser')

                select_tbody = soup.find_all('tbody')
                self.id = []
                for tbody in select_tbody:
                    if "site_td3" in str(tbody):
                        select_element = tbody.find(
                            'select',
                            style="display: none;",
                            id=lambda value: value and value.startswith('orderCount')
                        )

                        if select_element is None:
                            self.id.append(None)
                        else:
                            _id = str(select_element).split('orderCount')[1].split('"')[0]
                            self.id.append(_id)

                self.id.reverse()
                print(str(datetime.now()) + "--" + str(self.id))

                self.serviceCategoryId = response.text.split("name='serviceCategory.id' value='")[1].split("'/>")[0]
                self.serviceContentId = response.text.split("name='serviceContent.id' value='")[1].split("'/>")[0]
                self.currentDate = response.text.split('name="currentDate" value=')[1].split("'/>")[0].replace("'", "")
                if any(item is not None for item in self.id):
                    break
            except Exception:
                pass
            time.sleep(random.uniform(refresh_time - 2, refresh_time - 1))

        return any(item is not None for item in self.id)

    def getlist(self, Time):
        if self.id[Time] is None:
            print("getlist:::该场次已无名额")
            sys.exit()

        params = {
            'serviceContent.id': self.serviceContentId,
            'serviceCategory.id': self.serviceCategoryId,
            'codeStr': '',
            'currentDate': str(self.currentDate),
            'resourceIds': self.id[Time],
            'orderCounts': '1',
        }
        cookies = {
            self.nsc_cookie_name: self.NSC_Xfc,
            'JSESSIONID': self.JSESSIONID,
        }
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Referer': 'https://elife.fudan.edu.cn/public/front/getResource2.htm?contentId=8aecc6ce780fe18301786c51f2a5627b&ordersId=&currentDate=2025-09-29',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        response = requests.get(
            'https://elife.fudan.edu.cn/public/front/loadOrderForm_ordinary.htm',
            params=params,
            cookies=cookies,
            headers=headers,
        )
        if 'id="order_user"' in response.text:
            self.name = response.text.split('id="order_user" name="orderuser" readOnly="readOnly" value="')[1].split('"')[0]
            self.rsa_text_ = response.text.split('id="rsa_text_" name="rsa_text_" value="')[1].split('"')[0]
            print("getlist:::获取订单成功")
        else:
            print("getlist:::订单获取异常")
            print("getlist:::", response.text)
            sys.exit()

    def getBase64img(self):
        url = 'https://elife.fudan.edu.cn/public/front/getClickValidateImg.htm'
        cookies = {
            self.nsc_cookie_name: self.NSC_Xfc,
            'JSESSIONID': self.JSESSIONID,
        }
        max_retries = 2
        timeout = 5
        last_err = None
        for attempt in range(max_retries + 1):
            try:
                resp = requests.get(url, cookies=cookies, headers=self.headers, timeout=timeout)
                if resp.status_code != 200:
                    raise RuntimeError(f"HTTP {resp.status_code}")

                try:
                    data = resp.json()
                except ValueError:
                    text = resp.text.strip()
                    raise RuntimeError("Response is not valid JSON", text[:200])

                if not data:
                    raise RuntimeError("API returned null/empty JSON")

                obj = data.get('object')
                if not obj or 'ValidImage' not in obj or 'ValidText' not in obj:
                    raise RuntimeError(f"Unexpected payload: {str(data)[:200]}")

                return obj['ValidImage'], obj['ValidText']

            except (RequestException, Timeout, RuntimeError) as e:
                last_err = e
                if attempt < max_retries:
                    continue
                raise RuntimeError(f"getBase64img failed after {max_retries+1} attempts: {last_err}")

    def base64Api1(self):
        img, ctt = self.getBase64img()
        data = {"username": 'zhouhanshu', "password": 'Zhs123456', "ID": '35484990', "b64": img,
                "version": "3.1.1"}
        data_json = json.dumps(data)
        result = json.loads(
            requests.post("http://www.fdyscloud.com.cn/tuling/predict", data=data_json).text)
        sizex = []
        for i in range(1, len(result['data']) + 1):
            sizex.append(str(result['data'][f'顺序{str(i)}']['X坐标值']) + ',' + str(
                result['data'][f'顺序{str(i)}']['Y坐标值']))
        return sizex

    def base64Api2(self):
        img, ctt = self.getBase64img()
        data = {"username": 'zhouhanshu', "password": 'Zhs123456', "typeid": 43, "image": img, "content": ctt}
        result = json.loads(requests.post("http://api.ttshitu.com/predict", json=data).text)
        if result['success']:
            result = result["data"]["result"]
        else:
            print('识别失败')
        sizex = result.split('|')
        return sizex

    def oververified(self):
        time1 = time.time()
        while True:
            while True:
                coords = self.base64Api2()
                if len(coords) == 4:
                    print(str(datetime.now()) + str(coords))
                    break
                else:
                    print(str(datetime.now()) + str(coords))
            coord_0 = coords[0].split(',')
            coord_1 = coords[1].split(',')
            coord_2 = coords[2].split(',')
            coord_3 = coords[3].split(',')
            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                codes_js_path = os.path.join(base_dir, 'codes.js')
                f = open(codes_js_path, 'r', encoding='utf-8').read()
                ctx = execjs.compile(f)
                result = ctx.call('__00157003', [int(coord_0[0]), int(coord_0[1])],
                                  [int(coord_1[0]), int(coord_1[1])],
                                  [int(coord_2[0]), int(coord_2[1])],
                                  [int(coord_3[0]), int(coord_3[1])])

                data = {
                    'code': result,
                }

                cookies = {
                    self.nsc_cookie_name: self.NSC_Xfc,
                    'JSESSIONID': self.JSESSIONID,
                }

                response = requests.post(
                    'https://elife.fudan.edu.cn/public/front/validateClickCode.htm',
                    cookies=cookies,
                    headers=self.headers,
                    data=data,
                )
                print(str(datetime.now()) + response.text)
                if "验证通过" in response.text:
                    break
            except FileNotFoundError:
                print("Failed to find codes.js at absolute path")
                time.sleep(100)
                exit()
        time3 = time.time()
        print(str(datetime.now()) + ":验证码耗时： " + str(time3 - time1))
        codes = json.loads(response.text)
        return codes['object']['code']

    def save_order(self, Time, mobile):
        cc = self.oververified()
        rsa = self.encrypt()
        self.headers['Content-Type'] = 'multipart/form-data; boundary=----WebKitFormBoundarycTcKgm1ZAqw1nEiN'
        params = {
            'op': 'order',
        }
        file = [
            ("moveEnd_X", ""),
            ("wbili", ""),
            ("validateCode", cc),
            ("serviceContent.id", self.serviceContentId),
            ("serviceCategory.id", self.serviceCategoryId),
            ("contentChild", ""),
            ("codeStr", ""),
            ("itemsPrice", ""),
            ("acceptPrice", ""),
            ("orderuser", self.name),
            ("rsa_text_", self.rsa_text_),
            ("text_", quote(self.rsa_text_ + '_' + rsa, safe='_')),
            ("resourceIds", self.id[Time]),
            ("orderCounts", "1"),
            ("lastDays", "0"),
            ("mobile", str(mobile)),
            ("d_cgyy.bz", "")
        ]
        m = MultipartEncoder(fields=file, boundary='----WebKitFormBoundarycTcKgm1ZAqw1nEiN')

        cookies = {
            self.nsc_cookie_name: self.NSC_Xfc,
            'JSESSIONID': self.JSESSIONID,
        }

        requests.post(
            'https://elife.fudan.edu.cn/public/front/saveOrderForCGYY.htm',
            params=params,
            cookies=cookies,
            headers=self.headers,
            data=m.to_string(),
        )
        # if "订单编号" in response.text:
        #     print("预约成功")
        # else:
        #     print("预约失败")


def main():
    # 生成预约链接
    leng = '&ordersId=&currentDate='
    current_date = datetime.now()
    target_date = current_date + timedelta(days=DAY_OFFSET)
    link = TARGET_URL + leng + target_date.strftime("%Y-%m-%d")

    print("预约链接：", link)
    Times = TIMES

    # 账号 & 密码加密
    content1 = str(username)
    raw_password = str(password)
    encrypted = rsa_encrypt(raw_password, pem_key)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    password_js_path = os.path.join(base_dir, 'password.js')
    f = open(password_js_path, 'r', encoding='utf-8').read()
    ctx = execjs.compile(f)
    content2 = ctx.call('c', encrypted)  # 加密后的密码
    content3 = str(link)

    # 多实例预登录
    Instances = {}
    for TimeVal in Times:
        instance_name = f"fd_{TimeVal}"
        Instances[instance_name] = {
            "instance": FD(content1, content2, content3),
            "time": TimeVal
        }

    print(str(datetime.now()))
    for name, data in Instances.items():
        try:
            fd = data["instance"]
            TimeVal = data["time"]
            fd.getgetLoction1()
            fd.getauthChainCode()
            fd.login()
            fd.login7()
            print(str(datetime.now()) + "--时间" + str(TimeVal) + "登录完成")
        except Exception:
            print('=====================================================')
            print(traceback.format_exc())
            print('=====================================================')
            pass

    # tempfd 用来抢前统一刷新场地信息
    tempfd = FD(content1, content2, content3)
    tempfd.getgetLoction1()
    tempfd.getauthChainCode()
    tempfd.login()
    tempfd.login7()
    print(str(datetime.now()) + "--全部登录完成")

    # 锁定脚本直到指定时间
    now = datetime.now()
    target_time = now.replace(hour=TRIGGER_HOUR,
                              minute=TRIGGER_MINUTE,
                              second=TRIGGER_SECOND,
                              microsecond=0)
    if now < target_time:
        wait_seconds = (target_time - now).total_seconds()
        print(str(datetime.now()) + f"--未到抢场时间，再等 {wait_seconds} 秒.")
        time.sleep(wait_seconds)

    print(str(datetime.now()) + "--脚本开始运行")

    # 刷新场地余量
    bool_ret = tempfd.get_tennis_place()
    if not bool_ret:
        print(str(datetime.now()) + "--当前无任何余量")
    zhs1 = tempfd.id
    zhs2 = tempfd.serviceCategoryId
    zhs3 = tempfd.serviceContentId
    zhs4 = tempfd.currentDate

    # 多实例并发抢
    start_time1 = time.time()
    for name, data in Instances.items():
        try:
            fd = data["instance"]
            TimeVal = data["time"]
            idx = TimeVal - 1  # 原脚本就是这样用的

            print('########################################')
            print(str(datetime.now()) + "--时间" + str(TimeVal) + "开始")
            print('########################################')

            fd.id = zhs1
            fd.serviceCategoryId = zhs2
            fd.serviceContentId = zhs3
            fd.currentDate = zhs4

            if fd.id[idx] is None:
                print(str(datetime.now()) + "--时间" + str(TimeVal) + "无余量")
                continue

            fd.getlist(idx)
            fd.save_order(idx, mobile)
            end_time1 = time.time()
            print(str(datetime.now()) + "--时间" + str(TimeVal) + "耗时：" + str(end_time1 - start_time1))
            time.sleep(0.8)

        except Exception:
            print('=====================================================')
            print(traceback.format_exc())
            print('=====================================================')
            time.sleep(0.8)
            pass


if __name__ == "__main__":
    main()
