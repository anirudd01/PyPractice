from random import randint
from time import sleep
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.background import BackgroundTasks


app = FastAPI(title="Random",debug=True)
NUMBER = 0

@app.get("/random",name="Simple Random Num Generator",deprecated=True)
def get_random():
    return JSONResponse({"data":randint(1,100)})

@app.get("/v1/random",name="Random Num Generator Along with Prev Sum")
def get_random():
    global NUMBER
    random_numb = randint(1,100)
    NUMBER += random_numb
    return JSONResponse({"number":random_numb,"sum":NUMBER},201)


def log_sleep_log(n):
    print(f"This is Log {n} Before 3 sec Sleep")
    sleep(3)
    print(f"This is Log {n} After 3 sec Sleep")

@app.get("/v2/random",name="Random Num Generator with bg task")
async def get_random_bg_task(bg_tasks:BackgroundTasks):
    random_numb = randint(1,100)
    bg_tasks.add_task(log_sleep_log,n=random_numb)
    return JSONResponse({"number":random_numb},background=bg_tasks)
