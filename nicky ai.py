import datetime
import sys
import time
import webbrowser
import os
import pyautogui
import pyttsx3
import speech_recognition as sr
import psutil

def initialize_engine():
    engine=pyttsx3.init("sapi5")
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)
    rate = engine.getProperty('rate')
    engine.setProperty('rate',rate-50)
    volume = engine.getProperty('volume')
    engine.setProperty('volume',volume+0.25) 
    return engine
def speak(text):
    engine=initialize_engine()
    engine.say(text)
    engine.runAndWait()
def command():
    r=sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source,duration=0.5)
        print("listening....",end="",flush=True)
        r.pause_threshold=1.0
        r.phrase_threshold=0.3
        r.sample_rate=48000
        r.dynamic_energy_threshold=True
        r.operation_timeout=5
        r.non_speaking_duration=0.5
        r.dynamic_energy_adjustment=2
        r.energy_threshold=4000
        r.phrase_time_limit=10
        #print(sr.Microphone.list_microphone_names())
        audio=r.listen(source)
    try:
        print("\r",end="",flush=True)
        print("recognising...",end="",flush=True)
        query=r.recognize_google(audio,language='en-in')
        print(f"User said : {query}\n")
    except Exception as e:
        print("say that again")
        return "none"
    return query
def cal_day():
    day=datetime.datetime.today().weekday()+1
    day_dict={
        1:"Monday",
        2:"Tuesday",
        3:"Wednesday",
        4:"Thursday",
        5:"Friday",
        6:"Saturday",
        7:"Sunday"
    }
    if day in day_dict.keys():
        day_of_week=day_dict[day]
        print(day_of_week)
    return day_of_week
def wishme():
    hour=int(datetime.datetime.now().hour)
    t=time.strftime("%I:%M:%p")
    day=cal_day()
    if(hour>=0) and (hour<=12) and ('AM' in t):
        speak(f"Good morning vishal,it's {day} and the time is {t}")
    elif(hour>=12) and (hour<=16) and ('PM' in t):
        speak(f"Good afternoon vishal,it's {day} and the time is {t}")
    else:
        speak(f"Good evening vishal,it's {day} and the time is {t}")
def song_play(command):
    if 'play superman'in command:
        speak("playing")
        webbrowser.open("https://www.youtube.com/watch?v=Mx_yZk47YN4")
    elif 'play without me'in command:
        speak("playing")
        webbrowser.open("https://www.youtube.com/watch?v=-8xhmV3JoG4")
    elif 'play die with a smile'in command:
        speak("playing")
        webbrowser.open("https://www.youtube.com/watch?v=Fid4joqj5bQ")
    elif 'play kadhal fail'in command:
        speak("playing")
        webbrowser.open("https://www.youtube.com/watch?v=RYV0qI2xfck")
    elif 'play badas'in command:
        speak("playing")
        webbrowser.open("https://www.youtube.com/watch?v=IqwIOlhfCak")
    
    
def social_media(command):
    if 'open facebook' in command:
        speak("opening your facebook")
        webbrowser.open("https://www.facebook.com/")
    elif 'open instagram'in command:
        speak("opening your instagram")
        webbrowser.open("https://www.instagram.com/")
    elif 'open discord' in command:
        speak("opening your discord")
        webbrowser.open("https://discord.com/")
    elif 'open whatsapp' in command:
        speak("opening your whatsapp")
        webbrowser.open("https://web.whatsapp.com/")
    elif 'open youtube' in command:
        speak("opening your youtube")
        webbrowser.open("https://www.youtube.com/")
    else:
        speak("no data")
def close_social(command):
    if 'close facebook' in command:
        speak("closing your facebook")
        pyautogui.hotkey('ctrl', 'w')
    elif 'close instagram'in command:
        speak("closing your instagram")
        pyautogui.hotkey('ctrl', 'w')
    elif 'close discord' in command:
        speak("closing your discord")
        pyautogui.hotkey('ctrl', 'w')
    elif 'close whatsapp' in command:
        speak("closing your whatsapp")
        pyautogui.hotkey('ctrl', 'w')
    elif 'close youtube' in command:
        speak("closing your youtube")
        pyautogui.hotkey('ctrl', 'w')
def schedule():
    day= cal_day().lower()
    speak("your today's schedule is")
    week={
    "monday":"from 8:00 am to 9:40 am you have statistics for engineers lab class , from 9:50 am to 11:30 am you have problem solving in oops lab class , from 11:40 am to 1:20 pm you have engneering chemistry lab class ,then you have 1 hour 40 minutes break, after that from 3:00 pm to 3:50 pm you have engneering chemistry theory class , from 4:00 pm to 4:50 pm you have soft skills class, from 5:00 pm to 5:50 pm you have data structure theory class, then finally from 6:00 pm to 6:50 pm you have statistics for engineers theory class.",
    "tuesday":"from 11:40 am to 1:20 pm you have technical english class , then 40 minutes lunch break , after that from 2:00 pm to 2:50 pm you have data structure theory class, from 3:00 pm to 3:50 pm you have statistics for engineers theory class, from 4:00 pm to 4:50 pm you have enivironmental science class, then finally from 5:00 pm to 5:50 pm you have discrete maths class.",
    "wednesday":"from 9:50 am to 11:30 am you have technical english class, then from 2.00 pm to 2:50 pm you have discrete maths class, from 4:00 pm to 4:50 pm you have engineering chemistry theory class, then finally from 5:00 pm to 5:50 pm you have soft skills class.",
    "thursday":"from 8:00 am to 9:40 am you have problem solving in oops lab class, then 2:00 pm to 2:50 pm you have soft skills class, from 3:00 pm to 3:50 pm you have data structure theory class, from 4:00 pm to 4:50 pm you have statistics for engineers theory class, from 5:00 pm to 5:50 pm you have environmental science class ,then finally from 6:00 pm to 6:50 pm you have discrete maths class.",
    "friday":"from 9:50 am to 11:30 am you problem solving in oops class ,from 11:40 am to 1:20 pm you have data structure lab class, from 2:00 pm to 2:50 pm you have environmental science class, from 3:00 pm to 3:50 pm you have discrete maths class, then finally from 5:00 pm to 5:50 pm you have engineering chemistry theory class .",
    "saturday":"it varies for every week.",
    "sunday":"it is holiday,but don't forget to complete your work."
    }
    if day in week.keys():
        speak(week[day])
def openapp(command):
    if "calculator" in command:
        speak("opening calculator")
        os.startfile('c:\\Windows\\system32\\calc.exe')
    elif "notepad" in command:
        speak("opening notepad")
        os.startfile('c:\\Windows\\system32\\notepad.exe')
    elif "this pc" in command:
        speak("opening this pc")
        os.startfile('explorer.exe')

        
def closeapp(command):
    if "calculator" in command:
        speak("closing calculator")
        pyautogui.hotkey('ctrl', 'w')
    elif "notepad" in command:
        speak("closing notepad")
        os.system('taskkill /f /im notepad.exe')
    elif "this pc" in command:
        speak("closing this pc")
        pyautogui.hotkey('ctrl', 'w')
def browsing(query):
    if 'browser' in query:
        speak("what should i search on browser..") 
        s=command().lower()
        webbrowser.open(f"{s}")
def condition():
    usage =(psutil.cpu_percent())
    speak(f"CPU is at {usage} percentage")
    battery=psutil.sensors_battery()
    percentage=battery.percent
    speak(f"our system have {percentage} percentage battery")






if __name__=="__main__":
    wishme()
    speak("how can i help you")
    while True:
        query=command().lower()
        #query=input("enter your command:")
        
        

        if(' open facebook' in query) or ('open instagram' in query) or ('open discord'in query) or ('open whatsapp' in query) or ('open youtube'in query):
            social_media(query)
        elif(' close facebook' in query) or ('close instagram' in query) or ('close discord'in query) or ('close whatsapp' in query) or ('close youtube'in query):
            close_social(query)
        elif ("my schedule" in query):
            schedule()
        elif("volume up"in query) or ("increase volume"in query):
            pyautogui.press("volumeup")
            speak("volume increased")
        elif("volume down"in query) or ("decrease volume"in query):
            pyautogui.press("volumedown")
            speak("volume decreased")
        elif("volume mute"in query) or ("mute the volume"in query):
            pyautogui.press("volumemute")
            speak("volume muted")
        elif("open calculator" in query) or ("open notepad" in query ) or ("open this pc" in query):
            openapp(query)
        elif("close calculator" in query) or ("close notepad" in query ) or ("close this pc" in query):
            closeapp(query)
        elif("open browser" in query):
            browsing(query)
        elif("system condition"in query) or ("condition of the system"in query):
            speak("checking the system condition")
            condition()
        elif("close")in query:
            speak("closing")
            pyautogui.hotkey('ctrl', 'w')
        elif('play superman' in query) or ('play die with a smile' in query) or ('play kadhal fail'in query) or ('play without me' in query) or ('play badas'in query):
            song_play(query)
        if query == "exit":
            speak("Bye, It was nice talking to you ")
            break
        

