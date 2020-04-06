import urllib.request, json
from pprint import pprint
import os
import time
url = os.environ["ARIA2URL"] if "ARIA2URL" in os.environ else "127.0.0.1:6800"
secret = os.environ["ARIA2SECRET"] if "ARIA2SECRET" in os.environ != "" else "secret"

running_tasks_queue = []
waiting_tasks_queue = []
partial_tasks_queue = {}
partial_tasks_ids = {}

def sendAria2Req(json_body_bytes):
    req = urllib.request.Request(
        "http://{0}/jsonrpc".format(url),
        data=json_body_bytes
    )
    req.add_header("Content-Type", "application/json; charset=utf-8")
    c = urllib.request.urlopen(req)
    ret = json.loads(c.read())
    # pprint(ret)
    return ret


def restartTask(task_enti):
    # restart a task requires getOption + addUri with the exact opions
    taskid = partial_tasks_ids[task_enti]
    jsonreq_get_option = json.dumps({
        "jsonrpc":"2.0", "id":"guardian",
        "method":"aria2.getOption",
        "params": ["token:{0}".format(secret), taskid]
    }).encode("utf-8")
    ret = sendAria2Req(jsonreq_get_option)
    opt = ret['result']
    # pprint(opt)
    print(task_enti[1])
    jsonreq_add_uri = json.dumps({
        "jsonrpc":"2.0", "id":"guardian",
        "method":"aria2.addUri",
        "params": ["token:{0}".format(secret), [task_enti[1]], opt]
    }).encode("utf-8")
    ret = sendAria2Req(jsonreq_add_uri)
    pprint(ret)

jsonreq_get_stopped = json.dumps({
    "jsonrpc":"2.0", "id":"guardian",
    "method":"aria2.tellStopped",
    "params": ["token:{0}".format(secret), -1, 1]
}).encode("utf-8")

jsonreq_get_active = json.dumps({
    "jsonrpc":"2.0", "id":"guardian",
    "method":"aria2.tellActive",
    "params": ["token:{0}".format(secret)]
}).encode("utf-8")

jsonreq_get_waiting = json.dumps({
    "jsonrpc":"2.0", "id":"guardian",
    "method":"aria2.tellWaiting",
    "params": ["token:{0}".format(secret), -1, 1]
}).encode("utf-8")

while True:
    running_tasks_queue.clear()
    waiting_tasks_queue.clear()
    partial_tasks_queue.clear()

    running_tasks_ret = sendAria2Req(jsonreq_get_active)
    running_tasks = running_tasks_ret["result"]
    # pprint(running_tasks)
    for tt in running_tasks:
        running_tasks_queue.append((tt['files'][0]['path'], tt['files'][0]['uris'][0]['uri']))
    # pprint(running_tasks_queue)

    waiting_tasks_ret = sendAria2Req(jsonreq_get_waiting)
    waiting_tasks = waiting_tasks_ret["result"]
    for tt in waiting_tasks:
        waiting_tasks_queue.append((tt['files'][0]['path'], tt['files'][0]['uris'][0]['uri']))
    # pprint(waiting_tasks_queue)

    stopped_tasks_ret = sendAria2Req(jsonreq_get_stopped)
    stopped_tasks = stopped_tasks_ret["result"]
    for tt in stopped_tasks:
        complete_length = int(tt["completedLength"])
        total_length = int(tt["totalLength"])
        download_percent = complete_length / total_length
        # if complete_length < total_length:
        f_path = tt['files'][0]['path']
        f_uri = tt['files'][0]['uris'][0]['uri']
        if (f_path, f_uri) in running_tasks_queue or (f_path, f_uri) in waiting_tasks_queue:
            print("task {0} is added, skipping".format(f_path))
            continue
        if (f_path, f_uri) not in partial_tasks_queue:
            if download_percent == 1:
                print("task {0} is completed, skipping")
            else:
                partial_tasks_queue[(f_path, f_uri)] = download_percent
                partial_tasks_ids[(f_path, f_uri)] = tt["gid"]
        else:
            if download_percent > partial_tasks_queue[(f_path, f_uri)]:
                partial_tasks_queue[(f_path, f_uri)] = download_percent
                print("task {0} new high percent {1}".format(f_path, download_percent))
    for tt in partial_tasks_queue:
        print("tasks: {0}".format(tt[0]))
    for tt in partial_tasks_queue:
        if partial_tasks_queue[tt] < 1:
            print("Found partial download {0} stopped at {1}".format(tt[0], partial_tasks_queue[tt]))
            restartTask(tt)
    time.sleep(60)
