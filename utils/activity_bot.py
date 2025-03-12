import json
import threading
import requests
import time
from datetime import datetime, timedelta
from utils.headers import HEADERS_LOGIN, HEADERS_ACTIVITY, HEADERS_ACTIVITY_INFO

lock = threading.Lock()
# 负责登录和报名操作
class ActivityBot:

    def __init__(self,userData):
        self.login_url = "https://apis.pocketuni.net/uc/user/login"
        self.activity_url = "https://apis.pocketuni.net/apis/activity/join"
        self.info_url = "https://apis.pocketuni.net/apis/activity/info"
        self.activity_list_url = "https://apis.pocketuni.net/apis/activity/list"
        self.userData = userData
        self.curToken = ""
        self.flag = {}
        self.debug = False
        

    def login(self):
        try:
            response = requests.post(self.login_url, headers=HEADERS_LOGIN, json=self.userData)
            response.raise_for_status()
            self.curToken = response.json().get("data", {}).get("token")
            if self.curToken:
                print("线程"+self.userData['userName']+"获取的Token:", self.curToken)
                return self.curToken
            else:
                raise ValueError("Token获取失败")
        except Exception as e:
            print("登录失败:", e)
            return None

    def signup(self, activity_id):
        cnt = 0
        while True:
            cnt += 1
            self.curToken = self.login()
            if self.curToken != None:
                break
            if cnt >= 5:
                break
        print("设置测试:")

        if not self.curToken:
            print("无法获取有效的Token, 报名中止")
            return

        data = {"activityId": activity_id}

        def send_request():
            if self.flag.get(activity_id) == True:
                return
            num = 5
            while num>0:
                num -= 1
                try:
                    headers = HEADERS_ACTIVITY.copy()
                    headers["Authorization"] = f"Bearer {self.curToken}" + ":" + str(self.userData.get("sid"))
                    response = requests.post(self.activity_url, headers=headers, json=data)
                    if response.status_code == 200:
                        print("请求成功,活动:",activity_id , response.text, "请求时间:" ,datetime.now())
                        if(response.text == '{"code":0,"message":"成功","data":{"msg":"PU君提示：报名成功，请留意活动签到时间哦~"}}'):
                            lock.acquire()
                            try:
                                self.flag[activity_id] = True
                            finally:
                                lock.release()

                        if(response.text == '{"code":9405,"message":"您已报名，请勿重复操作","data":{}}'):
                            lock.acquire()
                            try:
                                self.flag[activity_id] = True
                            finally:
                                lock.release()
                        break
                    else:
                        print("报名尝试失败:", response.text)
                        time.sleep(0.1)  # Maintain a short delay to avoid being blocked by the server
                except Exception as e:
                    print("报名过程中出错:", e)
                    time.sleep(0.1)  # Error handling with short delay
            if num == 0:
                print("报名失败")
        current_time = datetime.now()
        start_time = self.get_join_start_time(activity_id)

        print(activity_id, "活动开始时间:", start_time, "当前时间:", current_time)
        if start_time is None:
            print("未能获取活动开始时间")
            return
        time_to_start = (start_time - current_time).total_seconds()
        print("活动开始时间:", start_time, "当前时间:", current_time, "距离开始时间:", time_to_start)
        if time_to_start <= 60:
            while True :
                self.curToken = self.login()
                if self.curToken != None:
                    break
        else :
            print(datetime.now(),"sleep:",time_to_start - 60)
            time.sleep(time_to_start - 60)

        current_time = datetime.now()
        time_to_start = (start_time - current_time).total_seconds()

        if time_to_start > 0:
            print(datetime.now(), "sleep:", time_to_start - 0)
            time.sleep(time_to_start - 0)

        for _ in range(3):
            threading.Thread(target=send_request).start()
            # time.sleep(0.5)
        for _ in range(10):
            if self.flag.get(activity_id) == True:
                break
            threading.Thread(target=send_request).start()
            time.sleep(1)
        # for _ in range(20):
        #     if self.flag.get(activity_id) == True:
        #         break
        #     threading.Thread(target=send_request).start()
        #     time.sleep(1)
        print("本活动报名结束:你看看成功了吗",activity_id)

    debugTime = datetime.now() + timedelta(seconds=15)

    def get_join_start_time(self, activity_id):
        if self.debug == True:
            return self.debugTime
        headers = HEADERS_ACTIVITY_INFO.copy()
        headers["Authorization"] = f"Bearer {self.curToken}" + ":" + str(self.userData.get("sid"))
        payload = {"id": activity_id}
        try:
            response = requests.post(self.info_url, headers=headers, json=payload)
            join_start_time_str = response.json().get("data", {}).get("baseInfo", {}).get("joinStartTime")
            # 允许报名
            if join_start_time_str:
                    return datetime.strptime(join_start_time_str, '%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(f"获取活动信息失败1：{e}")
        return None
    
    #判断是否允许报名 然后进行本地化存储
    def is_allow_signup(self, activity_id):
        headers = HEADERS_ACTIVITY_INFO.copy()
        headers["Authorization"] = f"Bearer {self.curToken}" + ":" + str(self.userData.get("sid"))
        payload = {"id": activity_id}
        try:
            allow_signup = False
            response = requests.post(self.info_url, headers=headers, json=payload)
            allowCollege = response.json().get("data", {}).get("baseInfo", {}).get("allowCollege")
            base_info = response.json().get("data", {}).get("baseInfo", {})
            joinEndTime = datetime.strptime(base_info.get("joinEndTime"),'%Y-%m-%d %H:%M:%S')
            for college in allowCollege:
                if college['id'] == self.userData.get('collegeId'):
                    if college['allowUserCount'] - college['joinUserCount'] > 0:
                        allow_signup = True
                        print("活动允许本学院报名")
                        break
            # 在继续判断tribe 如果又tribe那么就得看是不是我们班的了
            allowTribe = base_info.get("allowTribe")
            if allowTribe != []:
                for tribe in allowTribe:
                    if tribe["name"] == "软件工程22-2":
                        allow_signup = True
                
            if allowCollege == [] and allowTribe == []:
                allow_signup  = True

            if joinEndTime < datetime.now():
                allow_signup = False

            if allow_signup:
                print("本活动允许报名")
                # 进行json存储
                # 先读取 再修改 再保存
                #如果一个 JSON 文件是空的（即文件内容为空，没有任何字符），
                # 在 Python 中使用 json.load 读取时会抛出 json.JSONDecodeError 异常。
                #后续改进一下 先判断有没有本文件再进行增加本文件。
                with open("ready_activity.json","r",encoding="utf-8") as file:
                    activity_data = json.load(file)
                #print(activity_data)
                # if activity_data is None:
                #     activity_data = []

                allow_activity_append = True
                # 后面要调试一下 防止空文件的入侵错误
                if activity_data != []:
                    for activity in activity_data:
                        if activity_id ==activity["activityId"]:
                            allow_activity_append = False
                            break
                collegeData = {
                            "name": base_info.get("name"),
                            "activityId": activity_id,
                            "categoryName": base_info.get("categoryName"),
                            "joinStartTime": base_info.get("joinStartTime"),
                            "joinEndTime":base_info.get("joinEndTime"),
                            "startTime": base_info.get("startTime"),
                            "endTime": base_info.get("endTime"),
                            "address": base_info.get("address"),
                        }
                if allow_activity_append:
                    activity_data.append(collegeData)
                with open("ready_activity.json","w",encoding="utf-8") as file:
                    json.dump(activity_data,file,indent=4,ensure_ascii=False)
                return True
            else:
                print("本活动不允许报名")
                return False
        except Exception as e:
            print(f"获取活动信息失败1：{e}")
            return False
        
    # 获取所有活动信息
    def get_all_activity(self):
        cnt = 0
        while True:
            cnt += 1
            self.curToken = self.login()
            if self.curToken != None:
                break
            if cnt >= 5:
                break
        print("设置测试:")

        if not self.curToken:
            print("无法获取有效的Token, 报名中止")
            return

        headers = HEADERS_ACTIVITY_INFO.copy()
        headers["Authorization"] = f"Bearer {self.curToken}" + ":" + str(self.userData.get("sid"))
        payload = {"sort":1,"page":1,"limit":30,"puType":0}
        try:
            response = requests.post(self.activity_list_url, headers=headers, json=payload)
            # OKK 我已经获取到了所有的活动信息，现在我要进行活动筛选 ，看看是否复合学院要求，同时我还有注意请求频率，一秒一次。
            # 但是我现在要先看看活动的信息，看看是否有我要的活动
            list = response.json().get("data", {}).get("list")
            for activity in list:
                print(activity.get("id"),activity.get("name"),"是否允许报名")
                time.sleep(1)
                if activity.get("startTimeValue") =="报名已结束":
                    print(activity.get("name"),"活动报名已经结束")
                    continue
                else:
                    self.is_allow_signup(activity.get("id"))
                print()

        except Exception as e:
            print(f"获取活动信息失败2：{e}")
        return None
