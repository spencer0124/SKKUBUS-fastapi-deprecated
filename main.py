from fastapi import FastAPI
import httpx

app = FastAPI()
a = 3
URL = "http://ws.bus.go.kr/api/rest/buspos/getBusPosByRouteSt?serviceKey=ORCkFmKr8bIoQOxjPIhZsu4xEumjEQFC9cFW%2Br6C026Yk2LMhxAsuEb%2BYVShmoMzD8HHW257I92FA8slrJUQMg%3D%3D&busRouteId=100900004&startOrd=1&endOrd=19&resultType=json"

@app.get("/bus/bus1")
def request():
    response = httpx.get(URL)
    return {'response': response.json()}


@app.get("/home/{name}")
def read_name(name:str):
    global a
    a += 1
    return {'name' : name}


@app.get("/home_err/{name}")
def read_name_err(name:int):
    return {'name' : name, 'v': a}

# run app
