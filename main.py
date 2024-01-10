from fastapi import FastAPI
import httpx
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from pytz import timezone
import re
from fastapi_utils.tasks import repeat_every
import logging


app = FastAPI()
a = 3
URL = "http://ws.bus.go.kr/api/rest/buspos/getBusPosByRouteSt?serviceKey=ORCkFmKr8bIoQOxjPIhZsu4xEumjEQFC9cFW%2Br6C026Yk2LMhxAsuEb%2BYVShmoMzD8HHW257I92FA8slrJUQMg%3D%3D&busRouteId=100900004&startOrd=1&endOrd=19&resultType=json"


### [성균관대학교 인사캠 셔틀버스] api

class HSSCBusAPIHandler:
    def __init__(self, url):
        self.url = url
        self.previous_data = {}
        self.refresh_count = 0

    def get_flag(self, car_number, event_date):
        if not car_number:
            return 0
        current_time = datetime.now(timezone('Asia/Seoul'))
        if event_date:
            event_time = datetime.fromisoformat(event_date)
            if (current_time - event_time).total_seconds() < 30:
                return 1
        return 2

    def process_data(self, data):
        new_data = []
        for item in data["items"]:
            item.pop('kind', None)
            item.pop('gpsLongitude', None)
            item.pop('gpsLatitude', None)
            item.pop('useTime', None)

            prev_data = self.previous_data.get(item['sequence'])
            if prev_data:
                if item['eventDate'] != prev_data['eventDate'] and item['carNumber'] != prev_data['carNumber']:
                    self.previous_data[item['sequence']]['eventDate'] = item['eventDate']
            
            item['flag'] = self.get_flag(item['carNumber'], item['eventDate'])
            new_data.append(item)
            self.previous_data[item['sequence']] = item

        self.refresh_count += 1
        return new_data

    async def update_bus_data(self):
        response = httpx.get(self.url)
        data = response.json()
        return self.process_data(data)


bus_handler_hssc = HSSCBusAPIHandler("https://kingom.skku.edu/skkuapp/getBusData.do?route=2009&_=1685209241816")
# bus_handler_hssc = BusAPIHandler("http://skkubus-api-test.kro.kr")

@repeat_every(seconds=10)  # Repeat every 10 seconds
async def periodic_update():
    await bus_handler_hssc.update_bus_data()
    try: 
        httpx.get('https://liveactivity-jongro-stationhewa-lgrkkmdl2q-uc.a.run.app')
    except Exception as e:
        logging.error(f"Error in first HTTP request: {e}")

@app.get("/bus/webviewlist")
def webviewlist():
    return {
    'totalcount': 1,
    'detail': {
        'item1': {
            'title': '설 연휴 귀향/귀경 버스',
            'subtitle': '지역별 왕복 운영',
            'type' : '성대',
            'effect' : True
        },
    }
}



@app.get("/bus/hssc")
async def bus_hssc():
    return {
        "refresh_count": bus_handler_hssc.refresh_count,
        "data": bus_handler_hssc.previous_data
    }




### [종로07] api
@app.get("/bus/jongro07")
def read_jongro07():
    return [
    {
        "stationId": 101,
        "name": "명륜새마을금고",
        "StationMessage": "정보 없음",
        "isFirstStation": True,
        "isLastStation": False,
        "isRotationStation": False,
        "iscurrentBusLocated": False,
        "exceedSecond": None,
        "carnumber": None
    },
    {
        "stationId": 102,
        "name": "서울국제고등학교",
        "StationMessage": "1개전",
        "isFirstStation": False,
        "isLastStation": False,
        "isRotationStation": False,
        "iscurrentBusLocated": True,
        "exceedSecond": 120,
        "carnumber": "1234AB"
    },
    {
        "stationId": 110,
        "name": "성균관대학교",
        "StationMessage": "3개전",
        "isFirstStation": False,
        "isLastStation": True,
        "isRotationStation": False,
        "iscurrentBusLocated": False,
        "exceedSecond": None,
        "carnumber": None
    }
]





### [종로07] [혜화역 1번 출구 정보] api

def parse_arrmsg(arrmsg):
    pattern_a_b = r"(\d+)분(\d+)초후\[(\d+)번째 전\]"
    pattern_b = r"(\d+)분후\[(\d+)번째 전\]"

    match_a_b = re.match(pattern_a_b, arrmsg)
    match_b = re.match(pattern_b, arrmsg)

    if match_a_b:
        minutes, seconds, _ = match_a_b.groups()
        total_seconds = int(minutes) * 60 + int(seconds)
        return {'case': 0, 'time': total_seconds, 'message': None}
    elif match_b:
        minutes, _ = match_b.groups()
        total_seconds = int(minutes) * 60
        return {'case': 0, 'time': total_seconds, 'message': None}
    else:
        return {'case': 1, 'time': None, 'message': arrmsg}



@app.get("/bus/jongro/stationHewa")
async def request():
     URL = "http://ws.bus.go.kr/api/rest/arrive/getArrInfoByRoute?ServiceKey=ORCkFmKr8bIoQOxjPIhZsu4xEumjEQFC9cFW%2Br6C026Yk2LMhxAsuEb%2BYVShmoMzD8HHW257I92FA8slrJUQMg%3D%3D&stId=100900075&busRouteId=100900004&ord=12&resultType=json"
     async with httpx.AsyncClient() as client:
        response = await client.get(URL)
        response_data = response.json()
        
        # Accessing the first item in the itemList array
        arrmsg1 = response_data.get("msgBody", {}).get("itemList", [{}])[0].get("arrmsg1", "")
        parsed_data = parse_arrmsg(arrmsg1)
        
        return {
            'title': 'stationHewa',
            'response': parsed_data
        }



###





@app.get("/home/{name}")
def read_name(name:str):
    global a
    a += 1
    return {'name' : name}


@app.get("/home_err/{name}")
def read_name_err(name:int):
    return {'name' : name, 'v': a}












### 성균관대학교 학식 정보 크롤링

# typeA: 공대식당
@app.get("/meal/nsc/typeA")
async def get_content():

    
    typeA_breakfast_url = "https://www.skku.edu/skku/campus/support/welfare_11_1.do?mode=info&srDt=2023-12-11&srCategory=B&conspaceCd=20201251&srResId=12&srShowTime=D"
    typeA_lunch_url = "https://www.skku.edu/skku/campus/support/welfare_11_1.do?mode=info&srDt=2023-12-11&srCategory=L&conspaceCd=20201251&srResId=12&srShowTime=D"
    typeA_dinner_url = "https://www.skku.edu/skku/campus/support/welfare_11_1.do?mode=info&srDt=2023-12-11&srCategory=D&conspaceCd=20201251&srResId=12&srShowTime=D"

    typeA_breakfast_response = requests.get(typeA_breakfast_url)
    typeA_lunch_response = requests.get(typeA_lunch_url)
    typeA_dinner_response = requests.get(typeA_dinner_url)

    menu_items = {
        "breakfast": process_response(typeA_breakfast_response),
        "lunch": process_response(typeA_lunch_response),
        "dinner": process_response(typeA_dinner_response)
    }
    
    return menu_items

def process_response(response):
    soup = BeautifulSoup(response.content, 'html.parser')
    corner_boxes = soup.find_all(class_="corner_box")

    items = []

    for box in corner_boxes:
        item = {}
        title_div = box.find(class_="menu_title")
        if title_div:
            item['title'] = title_div.get_text(strip=True)
        
        price_span = box.find('span', text=lambda x: x and '가격 :' in x)
        if price_span:
            price_text = price_span.text.replace('가격 :', '').strip()
            item['price'] = price_text
        
        if item:
            items.append(item)

    return items


# typeB: 교직원식당(구시재)

# typeC: 학생식당(행단골)


#


@app.get("/meals/today")
async def get_today_meals():
    url = "https://dorm.skku.edu/_custom/skku/_common/board/schedule_menu/food_menu_page.jsp?date=2023-12-14&board_no=61&lng=ko#a"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        return {"error": str(e)}

    soup = BeautifulSoup(response.content, 'html.parser')

    meals = {
        "breakfast": [],
        "lunch": [],
        "dinner": []
    }

    def extract_time_and_menu(description):
        parts = description.split(',', 1)
        if len(parts) == 2:
            time, menu = parts
        else:
            time = "Unknown time"
            menu = description
        return time, menu

    def extract_meals(div_id):
        meal_list = []
        meal_div = soup.find(id=div_id)
        for item in meal_div.find_all("li"):
            title_span = item.find("span", class_="board-menu-title01") or item.find("span", class_="board-menu-title02") or item.find("span", class_="board-menu-title03")
            title = title_span.get_text(strip=True) if title_span else "No title provided"
            description = item.find("p").get_text(strip=True) if item.find("p") else "No description provided"

            time, menu = extract_time_and_menu(description)
            meal_list.append({
                "title": title,
                "time": time,
                "menu": menu
            })
        return meal_list

    meals["breakfast"] = extract_meals("foodlist01")
    meals["lunch"] = extract_meals("foodlist02")
    meals["dinner"] = extract_meals("foodlist03")

    return meals




# run app
