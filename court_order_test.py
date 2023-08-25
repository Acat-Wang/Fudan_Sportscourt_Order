# coding=utf-8
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import datetime
import base64
import json
import requests
import urllib.request
import random
import cv2
import numpy as np
import configparser


#读取配置信息
config = configparser.ConfigParser()
config.read('config.ini')
myusername = config.get('credentials', 'username')
mypassword = config.get('credentials', 'password')

#定义IYYU的密钥
IYUU_TOKEN = config.get('credentials', 'IYUU')

refresh_internal = 2
refresh_count = 40
order_today = False



#定义IYYU信息发送函数
def iyuu(IYUU_TOKEN):
    url = f"https://iyuu.cn/{IYUU_TOKEN}.send"
    headers = {'Content-type': 'application/x-www-form-urlencoded'}
    def send(text, desp=""):
        Form = {'text': text, 'desp': desp}
        return requests.post(url, data=Form, headers=headers, verify=False)        
    return send

iy_info = iyuu(IYUU_TOKEN)

# 定义一个函数，根据今天是周几来点击不同的按钮
def click_button_by_weekday():

    # 获取今天是周几，返回一个数字，0 表示周一，6 表示周日
    weekday = datetime.datetime.today().weekday()
    # 如果是周五或周六或周日，就跳转到下一周，点击 id 为 "one1" 的按钮
    if weekday == 4 or weekday == 5 or weekday == 6:
        button = driver.find_element(By.CLASS_NAME, "right")
        button.click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "site_top")))

        # 定位到日期列表，并点击对应的日期，使用 By.CLASS_NAME 和 By.TAG_NAME 方法
        date_items = driver.find_element(By.ID, "one1")
        date_items.click()
        print("今天是周末，点击了第一个按钮。")

    # 如果是周二或周三，就点击 id 为 "one4" 的按钮
    elif weekday == 1:
        date_items = driver.find_element(By.ID, "one4")
        date_items.click()
        print("今天是周二，点击了第四个按钮。")

    elif weekday == 0:
        date_items = driver.find_element(By.ID, "one3")
        date_items.click()
        print("今天是周一, 点击了第3个按钮。")

#    如果是周二或周三，就点击 id 为 "one4" 的按钮
    # elif weekday == 0:
    #     date_items = driver.find_element(By.ID, "one1")
    #     date_items.click()
    #     print("今天是周一，点击了第一个按钮。")
    # 如果是别的时间，就什么也不干

    else:
        print("今天不需要预约场地。")

#定义一个函数，用api处理图片验证码
def base64_api_string(uname, pwd, img, typeid):
    with open(img, 'rb') as f:
        base64_data = base64.b64encode(f.read())
        b64 = base64_data.decode()
    data = {"username": uname, "password": pwd, "typeid": typeid, "image": b64}
    result = json.loads(requests.post("http://api.ttshitu.com/predict", json=data).text)
    if result['success']:
        return result["data"]["result"]
    else:
        #！！！！！！！注意：返回 人工不足等 错误情况 请加逻辑处理防止脚本卡死 继续重新 识别
        return result["message"]
    return ""

# 创建一个 WebDriver 对象
driver = webdriver.Edge()

# 打开指定的网址
driver.get("https://elife.fudan.edu.cn/public/front/toResourceFrame.htm?contentId=8aecc6ce749544fd01749a31a04332c2")

# 点击校内师生登录按钮
login_button = driver.find_element(By.CLASS_NAME, "xndl")
login_button.click()

# 等待页面加载完成
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username")))
time.sleep(random.uniform(2, 3))

# 输入用户名和密码
username = driver.find_element(By.ID, "username")
password = driver.find_element(By.ID, "password")
username.send_keys(myusername)
password.send_keys(mypassword)

# 点击登录按钮
login_button = driver.find_element(By.ID, "idcheckloginbtn")
login_button.click()

if driver.find_elements(By.ID, "captchaImg"):
    for _ in range (5):
        try:
            password = driver.find_element(By.ID, "password")
            password.send_keys("wang2222.")
            #time.sleep(random.uniform(1, 2))
            checkcodeimg = driver.find_element(By.ID,"captchaImg")
            # src = checkcodeimg.get_attribute("src")
            checkcodeimg_b64 = checkcodeimg.screenshot("checkcode.jpg")
            # response = requests.get(src).content
            # resposne_encode = base64.b64encode(response) # 对内容进行base64编码
            # src = "data:image/jpg;base64," + resposne_encode.decode("utf-8") # 拼接成data URI格式
            checkresult = base64_api_string(uname='acatwang', pwd='cfrubBMy5X', img="checkcode.jpg", typeid=3)
            checkcoderesp = driver.find_element(By.ID,"captchaResponse")
            checkcoderesp.send_keys(checkresult)
            login_button = driver.find_element(By.ID, "idcheckloginbtn")
            login_button.click()
            WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.ID, "con_one_1")))
            break
        except:
            driver.refresh()


# 根据日期和时间，找到对应的可预约按钮，并点击
start_time = "16:00" # 你想要预约的开始时间，格式为 hh:mm
end_time = "19:00" # 你想要预约的结束时间，格式为 hh:mm

# 计算时间在列表中的索引（从0开始）
start_hour = int(start_time[:2])
end_hour = int(end_time[:2])

# 调用 click_button_by_weekday 函数
if order_today:
    driver.refresh()
else:
    click_button_by_weekday()

# 等待页面加载完成
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "con_one_1")))
today_url = driver.current_url

#定义预约结果字符串
order_result = ""

for hour in reversed(range(start_hour, end_hour)):
    found_flag = False
                    
    if hour < 21:
        text_end_time = '{:0>2d}:00'.format(hour+1)
    else:
        text_end_time = '{:0>2d}:30'.format(hour+1)
    
    text_start_time = '{:0>2d}:00'.format(hour)

    for _ in range (refresh_count):
        try:
            # 等待页面加载完成
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "con_one_1")))
            # 找到所有的class为site_td1的元素，并且返回时间列表
            time_list = driver.find_elements(By.CLASS_NAME,'site_td1')
            for tr_element in driver.find_elements(By.CSS_SELECTOR, ".site_tr"):
                times = tr_element.find_elements(By.CSS_SELECTOR, ".site_td1")
                if len(times) > 0:
                    time_element = times[0]
                else:
                    continue
                text = time_element.text
                
                if text_start_time in text and text_end_time in text:
                    # 找到表格行中的最右边的按钮
            
                    order_button = tr_element.find_element(By.CSS_SELECTOR, "img[onclick]")
                    #order_button = tr_element.find_element(By.XPATH, '//img [starts-with(@onclick,"checkUser")]')

                    # 设置标志变量为True，表示找到了符合条件的元素，并点击
                    order_button.click()
                    found_flag = True
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "verify_button")))
                    verify_button = driver.find_element(By.ID, "verify_button")
                    verify_button.click()
                    print(datetime.datetime.now())
                    print('场地刷新')
                    break
            break
        except:
            time.sleep(random.uniform(refresh_internal, refresh_internal*2))
            driver.refresh()
            
    ordered_flag = False

    if found_flag:
        # 将滑块沿着水平方向移动offset个像素，沿着垂直方向不变
        for _ in range(5):
            try:
                #找到验证码元素，下载图片并用opencv处理
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "scream")))
                #time.sleep(random.uniform(0.1, 0.2))
                checkcode = driver.find_element(By.ID,"scream")
                src = checkcode.get_attribute("src")
                b64_data = src[len("data:image/jpg;base64,"): ]
                img_data = base64.b64decode(b64_data)
                img = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_COLOR)
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                lower_lmt = np.array([0, 0, 190])
                upper_lmt = np.array([0, 0, 194])
                mask = cv2.inRange(hsv, lower_lmt, upper_lmt)
                kernel = np.ones((3, 3), np.uint8) # 定义一个3x3的核
                opening = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel) # 对掩码进行开运算，去除小的噪声点
                contours, hierarchy = cv2.findContours(opening, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) # 对掩码进行轮廓检测，返回轮廓列表和层次结构
                (x, y) , radius = cv2.minEnclosingCircle(contours[0])
                #slide_result = base64_api(uname='acatwang', pwd='cfrubBMy5X', img=src, typeid=19, remark='请点击目标缺口的中心位置')

                #移动滑块
                slider = driver.find_element(By.CLASS_NAME,"slider-btn")
                
                # 在滑块元素上按住鼠标左键，不释放
                ActionChains(driver).click_and_hold(slider).perform()

                # 等待一段随机时间，模拟真人反应
                #time.sleep(random.uniform(0.1, 0.2))
                offset = int(x) / 469 * 270 - 14
                ActionChains(driver).drag_and_drop_by_offset(slider, offset, 0).perform()
                
                # 释放鼠标左键
                ActionChains(driver).release().perform()
                time.sleep(random.uniform(0.1, 0.2))
                # 点击预约
                order_button = driver.find_element(By.ID,"btn_sub")
                order_button.click()
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "order_table_td1")))
                ordered_flag = True
                break
            except:
                #time.sleep(random.uniform(0.1, 0.2))
                if driver.find_elements(By.CLASS_NAME, "pop_content"):
                    break

                elif driver.find_elements(By.CSS_SELECTOR, ".re-btn"):
                    reset_button = driver.find_element(By.CSS_SELECTOR, ".re-btn")
                    reset_button.click()

                elif driver.find_elements(By.ID, "verify_button"):
                    verify_button = driver.find_element(By.ID, "verify_button")
                    verify_button.click()
                    
                elif driver.find_elements(By.ID,"btn_sub"):
                    order_button = driver.find_element(By.ID,"btn_sub")
                    order_button.click()
                    break

    # 判断标志变量是否为False，表示没有找到符合条件的元素
    if ordered_flag:
        print(f"恭喜你，预约 {hour}:00-{hour+1}:00 成功！")
        order_result = order_result + f"恭喜你，预约 {hour}:00-{hour+1}:00 成功！\n"
    else:
        print(f"很遗憾，预约 {hour}:00-{hour+1}:00 失败！")
        order_result = order_result + f"很遗憾，预约 {hour}:00-{hour+1}:00 失败！\n"
    
    #time.sleep(random.uniform(0.1, 1))
    driver.get(today_url)

#发送预约结果
timenow = datetime.datetime.now()
timenow_text = timenow.strftime('%Y年%m月%d日%H:%M:%S') 
order_result = order_result + '\n' +timenow_text
iy_info("羽毛球场预约", order_result)

# 关闭浏览器
driver.quit()