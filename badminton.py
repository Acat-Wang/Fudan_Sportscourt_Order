import configparser
import json
import requests
import time
import datetime
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
#from PIL import Image, ImageDraw, ImageFont
import multiprocessing

def base64_api(uname, pwd, img, typeid, ctt):
    data = {"username": uname, "password": pwd, "typeid": typeid, "image": img, "content": ctt}
    result = json.loads(requests.post("http://api.ttshitu.com/predict", json=data).text)
    if result['success']:
        return result["data"]["result"]
    else:
        #！！！！！！！注意：返回 人工不足等 错误情况 请加逻辑处理防止脚本卡死 继续重新 识别
        return result["message"]
    return ""
#基础参数设置
order_today = False
if order_today :
    refresh_count = 2000
    refresh_delay = 30
else:
    refresh_count = 200
    refresh_delay = 2
#读取账号密码
config = configparser.ConfigParser()
config.read('config.ini')
myusername = config.get('credentials2', 'username')
mypassword = config.get('credentials2', 'password')
myurl = "https://elife.fudan.edu.cn/public/front/toResourceFrame.htm?contentId=8aecc6ce749544fd01749a31a04332c2"
font_path = "simsun.ttc"
font_size = 37

class Tennis(object):
    def __init__(self,start_time,end_time,id):
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 5)
        self.url = myurl
        self.start_hour = int(start_time[:2])
        self.end_hour = int(end_time[:2])
        self.id=id

    def click(self, xpath):
        self.wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()

    def zhslogin(self):
        #登录进入预约界面
        xpath = '//*[@id="login_table_div"]/div[2]/input'
        self.wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()#点击校内人员登录
        xpath = '//*[@id="username"]'
        self.wait.until(EC.presence_of_element_located((By.XPATH, xpath))).send_keys(myusername)
        xpath = '//*[@id="password"]'
        self.wait.until(EC.presence_of_element_located((By.XPATH, xpath))).send_keys(mypassword)
        xpath = '//*[@id="idcheckloginbtn"]'
        self.wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()
    
    def orderbyday(self):
        if datetime.datetime.today().weekday()>4:
            xpath = '/html/body/div[2]/div[2]/div[1]/ul/li[10]'
            self.click(xpath)
            print("进程"+str(self.id)+":抢下一周的")
        if order_today == True:
            weekday = (1+datetime.datetime.today().weekday())%7
        else:
            weekday = (3 + datetime.datetime.today().weekday())%7

        if weekday == 0:
            weekday = weekday + 7
        id = "one"+str(weekday)
        self.wait.until(EC.presence_of_element_located((By.ID, id))).click()
        print("进程"+str(self.id)+":抢周"+str(weekday))
        self.wait.until(EC.presence_of_element_located((By.ID, "con_one_1")))
        return self.driver.current_url

    def orderbyh(self,hour):
        found_flag = False
        current_url = self.driver.current_url
        #根据时间来抢
        text_end_time = '{:0>2d}:00'.format(hour+1)
        text_start_time = '{:0>2d}:00'.format(hour)
        for _ in range (refresh_count):
            try:
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "con_one_1")))
                for tr_element in self.driver.find_elements(By.CSS_SELECTOR, ".site_tr"):
                    times = tr_element.find_elements(By.CSS_SELECTOR, ".site_td1")
                    if len(times) > 0:
                        time_element = times[0]
                    else:
                        continue
                    text = time_element.text
                    if text_start_time in text and text_end_time in text:
                        tr_element.find_element(By.CSS_SELECTOR, "img[onclick]").click()
                        print(str(datetime.datetime.now())+"进程"+str(self.id)+":预约按钮点击完成")
                        found_flag = True
                        self.wait.until(EC.presence_of_element_located((By.XPATH,'//*[contains(@id,"verify_button")]'))).click()
                        print(str(datetime.datetime.now())+"进程"+str(self.id)+":验证码按钮点击完成，正在识别验证码")
                        break
                break
            except:
                time.sleep(refresh_delay)
                self.driver.get(current_url)
                print(str(datetime.datetime.now())+"进程"+str(self.id)+":无余量，刷新页面")
        return found_flag

    def tennis(self):
        self.driver.get(self.url)
        time.sleep(0.5)
        print(str(datetime.datetime.now())+"进程"+str(self.id)+":等待登录")
        self.zhslogin()#登录
        print(str(datetime.datetime.now())+"进程"+str(self.id)+":登录完成")

        # Get the current time
        now = datetime.datetime.now()

        # Set the target time to 6:59 a.m. on the same day
        target_time = now.replace(hour=6, minute=59, second=0, microsecond=0)

        # Check if the current time is earlier than 6:59 a.m.
        if now < target_time:
            print(f"Current time is earlier than 6:59 a.m. Waiting for 60 seconds.")
            # Wait 1 min
            time.sleep(60)

        today_url = self.orderbyday()#选择要抢的日期
        print(str(datetime.datetime.now())+"进程"+str(self.id)+":日期点击完成")
        
        # Get the current time
        now = datetime.datetime.now()

        # Set the target time to 6:59:58 a.m. on the same day
        target_time = now.replace(hour=6, minute=59, second=58, microsecond=0)

        # Check if the current time is earlier than 6:59:58 a.m.
        if now < target_time:
            # Calculate the number of seconds to wait
            wait_seconds = (target_time - now).total_seconds()
            print(f"Current time is earlier than 7 a.m. Waiting for {wait_seconds} seconds.")
            # Wait until 6:59:58 a.m.
            time.sleep(wait_seconds)
        start_time1 = time.time()
        print(datetime.datetime.now())
        #进入今天的预约界面，不断刷新，直到点击预约
        for hour in reversed(range(self.start_hour, self.end_hour)):
            
            self.orderbyh(hour)          #是否找到要预约的时间 

            ###################################################################
            #开始处理验证码并预约
            ###################################################################
            start_time2 = time.time()
            for i in range (10):
                self.wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[7]/div[2]/div[2]/div/div[1]/div[1]/img")))
                print(str(datetime.datetime.now())+"进程"+str(self.id)+":验证码图片加载完成")
                for j in range (10):
                    time.sleep(0.2)
                    checkcode = self.driver.find_element(By.XPATH, "/html/body/div[7]/div[2]/div[2]/div/div[1]/div[1]/img")
                    src = checkcode.get_attribute("src")
                    if src != None:
                        break
                    else:
                        reset_button = self.driver.find_element(By.CLASS_NAME, "valid_refresh")
                        reset_button.click()
                pdata = src[len("data:image/jpg;base64,"): ]
                checkcode_text = self.driver.find_element(By.CSS_SELECTOR,'body > div.valid_popup > div.valid_modal > div.valid_modal__body > div > div.valid_control > div > span.valid_tips__text > b').text
                #############################################################
                #输入验证码图片
                #############################################################
                print(str(datetime.datetime.now())+"进程"+str(self.id)+":验证码图片发送云端")
                result = base64_api(uname='acatwang', pwd='cfrubBMy5X', img=pdata, typeid=43, ctt=checkcode_text)
                result_list = result.split('|')
                if len(result_list) == 4:
                    print(str(datetime.datetime.now())+"进程"+str(self.id)+":验证码图片识别完成")
                    ###################################################################
                    #完成验证码点选
                    ###################################################################
                    half_width = float(checkcode.rect['width'])/2
                    half_height = float(checkcode.rect['height'])/2
                    for i in result_list:
                        lx = int(i.split(',')[0])
                        ly = int(i.split(',')[1])
                        ActionChains(self.driver).move_to_element_with_offset(checkcode,lx-half_width,ly-half_height).click().perform()
                    time.sleep(0.5)
                    popup = self.driver.find_element(By.XPATH, '/html/body/div[7]')
                    if not popup.is_displayed():
                        print(str(datetime.datetime.now())+"进程"+str(self.id)+":验证码图片识别成功")
                        break
                print(str(datetime.datetime.now())+"进程"+str(self.id)+":重新加载验证码")
                reset_button = self.driver.find_element(By.CLASS_NAME, "valid_refresh")
                reset_button.click()
            end_time1 = time.time()
            print("进程"+str(self.id)+":总计耗时"+str(end_time1-start_time1)+"s")
            print("进程"+str(self.id)+":验证码耗时"+str(end_time1-start_time2)+"s")
            #点击预约按钮
            self.click('//*[@id="btn_sub"]')
            print(f"恭喜你，预约 {hour}:00-{hour+1}:00 完成！")
            self.driver.get(today_url)

def worker(start_time,end_time,id):
    # 重要区别，创建对象的过程是在worker中完成，而不是在主进程中
    for loop_var in range(5):
        try:
            T = Tennis(start_time,end_time,id)
            T.tennis()
            break
        except:
            print("进程"+str(id)+"错误，重启")

if __name__ == '__main__':
    p1 = multiprocessing.Process(target=worker,args=("16:00", "17:00",1))
    p2 = multiprocessing.Process(target=worker,args=("17:00", "18:00",2))
    p3 = multiprocessing.Process(target=worker,args=("18:00", "19:00",3))

    p1.start()
    p2.start()
    p3.start()
    
    p1.join()
    p2.join()
    p3.join()
