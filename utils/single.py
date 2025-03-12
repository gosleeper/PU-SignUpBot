"""
对单独账号的抢活动
"""
import threading
from utils.activity_bot import ActivityBot
import queue


def single_account(user_data:dict,file_path = "activity_ids.txt"):
    print('线程：'+user_data['userName'])
    pass
    bot = ActivityBot(user_data)
    try:
        # with open(file_path, 'r') as file:
        #     activity_ids = [int(line.strip()) for line in file if line.strip()]
        from queue_manager import ACTIVITY_queue
        print("zheli")
        ACTIVITY = ACTIVITY_queue.get()
        print("活动ID列表：",ACTIVITY)
        activity_ids = ACTIVITY.copy()
        threads = []
        for activity_id in activity_ids:
            thread = threading.Thread(target=bot.signup, args=(activity_id,))
            print(activity_id,"开始执行线程")
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()
    except FileNotFoundError:
        print("线程："+user_data['userName']+"活动ID文件不存在")

# 设置一个默认用来更新的账号
def update_activities(user_data ={
        "userName": "202211070519",
        "password": "@qwer123456",
        "sid": 208754666766336,
        "device": "pc"
    }):
    bot = ActivityBot(user_data)
    bot.get_all_activity()
