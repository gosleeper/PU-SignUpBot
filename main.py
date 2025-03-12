from datetime import datetime, timedelta
import json
import threading
import queue
import pytz
from utils.user_data_manager import UserDataManager
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
import logging
from utils.single import update_activities
from apscheduler.triggers.cron import CronTrigger

logging.basicConfig(
    format="%(asctime)s - %(levelname)s: %(message)s",
    level=logging.INFO
)

def load_activities():
    with open("read_activity.json","r",encoding='utf-8')as file:
        return json.load(file)

# 负责记录立马要开始的活动
lock = threading.Lock()
def jobB():
    #调度器A定时任务
    #计算任务的时差是否小于33分钟。
    ACTIVITY = []

    print("调度器B定时任务计算时差")
    with open("ready_activity.json","r",encoding='utf-8') as file:
        activities = json.load(file)
    activity_data = activities.copy()
    run_time = datetime.now()
    for activity in activities:
        join_start_time = datetime.strptime(activity['joinStartTime'], '%Y-%m-%d %H:%M:%S')
        joinEndTime = datetime.strptime(activity['joinEndTime'], '%Y-%m-%d %H:%M:%S')
        if join_start_time - datetime.now() <= timedelta(minutes=12) and joinEndTime >= datetime.now():
            ACTIVITY.append(activity["activityId"])
            print("活动已经加入")
            #print(activity)
            activities.remove(activity)
            #run_time = join_start_time
    print(ACTIVITY)
    from queue_manager import ACTIVITY_queue
    ACTIVITY_queue.put(ACTIVITY)
    if len(activity_data) != len(activities):
        with open("ready_activity.json","w",encoding='utf-8') as file:
            json.dump(activities,file,indent=4)
    if ACTIVITY != []:
        scheduler.add_job(
            jobC,
            'date',
            run_date=run_time ,#- timedelta(minutes=1)
            replace_existing=True
        )
        scheduler.start()
        #更新活动列表json文件
        update_activities()
    else:
        print("没有活动")
    

def jobA():
    #负责更新活动列表
    update_activities()

def jobC():
    #负责执行抢任务
    print("调度器C定时任务执行抢任务")
    user_data_file = 'user_data.json'
    user_manager = UserDataManager(user_data_file)

    if not user_manager.user_datas:
        print("无用户数据！")
        user_manager.user_datas = []
    else:
        print("用户数据：")
        for user in user_manager.user_datas:
            print(user['userName'])
    user_manager.process_users()

def main():
    user_data_file = 'user_data.json'
    user_manager = UserDataManager(user_data_file)

    if not user_manager.user_datas:
        print("无用户数据！")
        user_manager.user_datas = []
    else:
        print("用户数据：")
        for user in user_manager.user_datas:
            print(user['userName'])

    add_user = input("是否新增用户 (y/n): ").strip().lower()
    if add_user == 'y':
        user_manager.add_new_user()
        user_manager.write_user_data()
    global scheduler
    scheduler = BlockingScheduler(timezone=pytz.timezone('Asia/Shanghai'))
    scheduler.add_job(jobA,'interval' ,id = 'jobA',hours=6,next_run_time=datetime.now())
    scheduler.add_job(jobB, 
                      'interval', 
                      minutes=11,
                      id='jobB',
                      next_run_time=datetime.now()
                      )
    scheduler.start()
    print("调度器已启动...")

# 让主线程保持运行
    try:
        threading.Event().wait()  # 等待直到手动终止
    except KeyboardInterrupt:
        print("程序退出，正在关闭调度器...")
        scheduler.shutdown()


if __name__ == "__main__":
    main()
