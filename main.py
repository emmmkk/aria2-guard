import urllib.request, json
from pprint import pprint
import os
import time
url = os.environ["ARIA2URL"] if "ARIA2URL" in os.environ else "127.0.0.1:6800"
secret = os.environ["ARIA2SECRET"] if "ARIA2SECRET" in os.environ != "" else "secret"

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


def restartTask(taskid):
    # restart a task requires getOption + addUri with the exact opions
    if taskid == "":
        raise RuntimeError("No task id specified")
    jsonreq_get_option = json.dumps({
        "jsonrpc":"2.0", "id":"guardian",
        "method":"aria2.getOption",
        "params": ["token:{0}".format(secret), taskid]
    }).encode("utf-8")
    ret = sendAria2Req(jsonreq_get_option)
    pprint(ret)

jsonreq_get_stopped = json.dumps({
    "jsonrpc":"2.0", "id":"guardian",
    "method":"aria2.tellStopped",
    "params": ["token:{0}".format(secret), -1, 1]
}).encode("utf-8")

while True:
    ret = sendAria2Req(jsonreq_get_stopped)
    tasks_status = ret["result"][0]

    # pprint(json.loads(c.read()))
    if int(tasks_status["completedLength"]) < int(tasks_status["totalLength"]):
        if "EOF" in tasks_status["errorMessage"] and "115" in tasks_status["files"][0]["uris"][0]['uri']:
            print("an 115 file is interrupted unexpectedly")
            # debug info
            for kk in tasks_status:
                if kk != "bitfield":
                    print("{0}: {1}".format(kk, tasks_status[kk]))
            # call restartTask
    time.sleep(100)
