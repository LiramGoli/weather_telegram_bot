import telebot
import json
import requests
import datetime
import time
what_to_wear_dict={25:"מכנס וחולצה קצרה",
                    18:"מכנס ארוך וחולצה ארוכה דקה או חולצה קצרה וג׳קט",
                    10:"מכנס ארוך חולצה ארוכה ומעיל",
                    -10:"אם אין לך ברירה אל תצא מהבית קר בטירוף\nתלבש ארוך ותקווה לטוב"}
cities_arr=[]
show_full=False
glob_weather=""

with open('city_list.json') as cities:
    city_list = json.load(cities)
    for i,city in enumerate(city_list):
        city_dict={"id":0,"name":"","order":0,"lat":0,"lon":0}
        city_dict["name"]=city["name"]
        city_dict["id"]=city["id"]
        city_dict["order"]=i+1
        city_dict["lat"]=city["coord"]["lat"]
        city_dict["lon"]=city["coord"]["lon"]
        cities_arr.append(city_dict)

weatherBot=telebot.TeleBot("5613765780:AAHGWkYU_eurN9SFIAikg4gBEznLU7Nw8fc")

@weatherBot.message_handler(commands=['start'])
def send_welcome(message):
	weatherBot.reply_to(message, "על מנת להתחיל, רשום את המילה ערים ולאחר מכן הקש את מספר העיר המבוקשת על מנת לקבל מידע על מזג האוויר בה")

@weatherBot.message_handler(content_types=["text"])
def preform_user_command(message):
    global show_full
    global glob_weather

    user_msg=message.text
    city=get_city(user_msg)

    if user_msg in ["ערים","show cities","cities","ערים אחי"]:
        msg="Choose your city's number"
        for city in cities_arr:
            msg+="\n"+str(city["order"])+")   "+city["name"]
        weatherBot.reply_to(message,msg)
    
    elif user_msg in ["כן","yes"] and show_full:
        msg=show_full_forecast(glob_weather)
        weatherBot.reply_to(message,msg)
        show_full=False
    
    elif user_msg in ["לא","no"] and show_full:
        msg="בסדר גמור"
        weatherBot.reply_to(message,msg)
        show_full=False

    #after knowing it's not string
    elif city != None:
        weather=get_api_call(city)
        glob_weather=weather
        show_full=True
        msg=analyze_data(weather)
        weatherBot.reply_to(message,msg)
        msg="מעוניין לראות תחזית מלאה?"
        time.sleep(1)
        weatherBot.reply_to(message,msg)
    
    else:
        msg="לא יודע מה לעשות עם מה שאמרת, בבקשה תרשום ערים או מספר עיר כדי להתחיל"
        weatherBot.reply_to(message,msg)

def get_city(msg):
    for city in cities_arr:
        if msg in str(city["order"]):
            return city
    return None

def get_api_call(city):
    api_url=f"""https://api.open-meteo.com/v1/forecast?latitude={city["lat"]}&longitude={city["lon"]}&hourly=temperature_2m,rain&daily=temperature_2m_max,temperature_2m_min&current_weather=true&timezone=auto"""
    response = requests.get(api_url)
    weather_dict={"curr_temp":"","max_temp":"","min_temp":"","hourly_weather":[]}
    now = datetime.datetime.now()

    #gathering all the info
    weather_dict["curr_temp"]=response.json()["current_weather"]["temperature"]
    weather_dict["max_temp"]=response.json()["daily"]['temperature_2m_max'][0]
    weather_dict["min_temp"]=response.json()["daily"]['temperature_2m_min'][0]

    hours=response.json()["hourly"]['time']
    temp_by_hours=response.json()["hourly"]['temperature_2m']
    rain_by_hours=response.json()["hourly"]["rain"]
    #gathering all hours and degrees

    for i in range (len(hours)):
        if(int(hours[i].split("T")[1].split(":")[0])>=now.hour)\
            and(int(hours[i].split("T")[0].split("-")[2])==now.day):
            weather_dict["hourly_weather"].append({"hour":hours[i].split("T")[1].split(":")[0],
                                            "temp":temp_by_hours[i],
                                            "rain":rain_by_hours[i]})
    
    return weather_dict

def analyze_data(weather):
    msg="\n"
    msg+=f"""הטמפרטורה הנמוכה ביותר: {weather["min_temp"]}\n"""
    msg+=f"""הטמפרטורה הגבוהה ביותר: {weather["max_temp"]}\n"""
    msg+=f"""הטמפרטורה עכשיו: {weather["curr_temp"]}\n"""

    chance_to_rain={}
    tmp_avg=0.
    rain_avg=0.

    if len(weather["hourly_weather"])>6:

        for i in range(0,6):
            tmp_avg+=float(weather["hourly_weather"][i]["temp"])
            rain_avg+=float(weather["hourly_weather"][i]["rain"])
            if weather["hourly_weather"][i]["rain"] >0.65:
                chance_to_rain["hour"]=weather["hourly_weather"][i]["hour"]
                chance_to_rain["rain"]=weather["hourly_weather"][i]["rain"]
        tmp_avg/=6
        rain_avg/=6

    else:

        for i in range(0,len(weather["hourly_weather"])):
            tmp_avg+=float(weather["hourly_weather"][i]["temp"])
            rain_avg+=float(weather["hourly_weather"][i]["rain"])
            if weather["hourly_weather"][i]["rain"] >0.65:
                chance_to_rain["hour"]=weather["hourly_weather"][i]["hour"]
                chance_to_rain["rain"]=weather["hourly_weather"][i]["rain"]

        tmp_avg/=len(weather["hourly_weather"])
        rain_avg/=len(weather["hourly_weather"])

    msg+="מומלץ ללבוש: "
    for key in what_to_wear_dict.keys():
        if tmp_avg>=key:
            msg+=what_to_wear_dict[key]
            break
    msg+="\n"

    if rain_avg<0.3:
        msg+="אין גשם\n"
    elif rain_avg<0.5:
        msg+="סיכוי נמוך לגשם\n"
    elif rain_avg<0.65:
        msg+="סיכוי בינוני לגשם\n"
    else: msg+="סיכוי גבוהה מאוד לגשם\n"

    if chance_to_rain!={}:
        msg+="סיכויים גבוהים לגשם בשעות: "
        for hour in chance_to_rain:
            msg+=hour+', '
    msg+="\n"

    return msg

def show_full_forecast(weather):
    msg="\n"
    for weth in weather["hourly_weather"]:
        msg+=f"""שעה: {weth["hour"]}:00 , טמפ:{weth["temp"]}, סיכוי לגשם:{weth["rain"]}\n"""
    return msg


    




weatherBot.polling()