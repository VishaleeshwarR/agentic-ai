from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import sys
import time
import webbrowser
import os
import pyautogui
import pyttsx3
import speech_recognition as sr
import pywhatkit
import psutil
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import create_tool_calling_agent, AgentExecutor
from tools import search_tool, wiki_tool, save_tool
import json
from rag_pipeline import RAGPipeline
import re
import textwrap
from datetime import datetime
import threading

# Load environment variables
if not load_dotenv():
    # Try parent directory
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


# Initialize global LLM for general queries
llm = ChatOpenAI(model="gpt-3.5-turbo")

# Initialize global agent for fallback
tools = [search_tool, wiki_tool, save_tool]
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant. Use tools if necessary to answer user queries. If a query is about a file, the RAG pipeline will handle it first, but if it fails, you should provide a general answer or search for info."),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{query}"),
    ("placeholder", "{agent_scratchpad}"),
])
agent = create_tool_calling_agent(llm=llm, prompt=prompt, tools=tools)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

def get_general_response(query, chat_history=None):
    if chat_history is None:
        chat_history = []
    try:
        response = agent_executor.invoke({"query": query, "chat_history": chat_history})
        return response.get("output", "I'm sorry, I couldn't process that query.")
    except Exception as e:
        print(f"Error in general agent: {e}")
        return f"Error: {str(e)}"

print("General agent initialized", flush=True)

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}) # Explicit CORS

# Initialize the text-to-speech engine
def initialize_engine():
    engine = pyttsx3.init("sapi5")
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate - 50)
    volume = engine.getProperty('volume')
    engine.setProperty('volume', volume + 0.25)
    return engine

def speak(text):
    engine = initialize_engine()
    engine.say(text)
    engine.runAndWait()

def command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.5)
        print("Listening...", end="", flush=True)
        r.pause_threshold = 1.0
        r.phrase_threshold = 0.3
        r.sample_rate = 48000
        r.dynamic_energy_threshold = True
        r.operation_timeout = 5
        r.non_speaking_duration = 0.5
        r.dynamic_energy_adjustment = 2
        r.energy_threshold = 4000
        r.phrase_time_limit = 10
        audio = r.listen(source)
    try:
        print("\r", end="", flush=True)
        print("Recognizing...", end="", flush=True)
        query = r.recognize_google(audio, language='en-in')
        print(f"User said: {query}\n")
    except Exception as e:
        print("Say that again")
        return "none"
    return query

# Music functionality (from music.py)
def play_music(query):
    song = query.replace("play", "").strip()
    speak(f"Playing {song}")
    pywhatkit.playonyt(song)

# Research paper functionality (from main.py)
def create_research_paper(query, chat_history=None):
    if chat_history is None:
        chat_history = []
    load_dotenv()

    class ResearchResponse(BaseModel):
        topic: str
        summary: str
        sources: list[str]
        tools_used: list[str]

    llm = ChatOpenAI(model="gpt-3.5-turbo")
    parser = PydanticOutputParser(pydantic_object=ResearchResponse)

    research_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are a research assistant that will help generate a research paper.
                Answer the user query and use necessary tools. 
                Wrap the output in this format and provide no other text\n{format_instructions}
                """,
            ),
            MessagesPlaceholder("chat_history"),
            ("human", "{query}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    ).partial(format_instructions=parser.get_format_instructions())

    research_agent = create_tool_calling_agent(
        llm=llm,
        prompt=research_prompt,
        tools=tools
    )

    research_executor = AgentExecutor(agent=research_agent, tools=tools, verbose=True)
    if("on" not in query):
        speak("Please provide the query in the format 'create research paper on [topic]'")
        return "Invalid query format."
    query_topic = query.split("on")[1].strip()
    print("Topic:", query_topic)

    raw_response = research_executor.invoke({"query": query_topic, "chat_history": chat_history})
    print("Raw Response Content:", raw_response.get("output", ""))

    try:
        # The LLM might return the JSON wrapped in markdown or just the raw JSON string
        content = raw_response['output']
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        data = json.loads(content)
        topic = sanitize_filename(data.get("topic", "research_paper"))
        summary = data.get("summary", "")
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{topic}_{timestamp}.txt"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"TOPIC: {data.get('topic', topic)}\n")
            f.write(f"DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-" * 50 + "\n\n")
            f.write(textwrap.fill(summary, width=100))
            f.write("\n\n" + "-" * 50 + "\n")
            f.write("SOURCES USED:\n")
            for source in data.get("sources", []):
                f.write(f"- {source}\n")
        
        return f"✅ Research paper on '{data.get('topic')}' has been created and saved as '{filename}'."
    except Exception as e:
        print(f"Error processing research paper: {e}")
        # Fallback: Save the raw output if JSON parsing fails
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"research_raw_{timestamp}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(raw_response.get("output", "No content generated."))
        return f"✅ Processed research, but had formatting issues. Saved raw content to '{filename}'."

    # try:
    #     structured_response = parser.parse(raw_response.get("output")[0]["text"])
    #     print("Research Paper Created:")
    #     print(structured_response)

    #     # Save the research paper to a file on the desktop
    #     desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    #     file_path = os.path.join(desktop_path, "research_paper.txt")
    #     with open(file_path, "w") as file:
    #         file.write(str(structured_response))

    #     speak(f"The research paper has been created and saved on your desktop as 'research_paper.txt'.")
    #     raise "Research paper created successfully."
    # except Exception as e:
    #     print("Error parsing response", e, "Raw Response - ", raw_response)

def sanitize_filename(filename: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

def cal_day():
    day = datetime.now().isoweekday()
    day_dict = {
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
    hour=int(datetime.now().hour)
    t=time.strftime("%I:%M:%p")
    day=cal_day()
    if(hour>=0) and (hour<=12) and ('AM' in t):
        speak(f"Good morning ,it's {day} and the time is {t}")
    elif(hour>=12) and (hour<=16) and ('PM' in t):
        speak(f"Good afternoon ,it's {day} and the time is {t}")
    else:
        speak(f"Good evening ,it's {day} and the time is {t}")

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

# Flask routes
@app.route('/play', methods=['POST'])
def play():
    data = request.json
    query = data.get('query', '')
    play_music(query)
    return jsonify({"response": f"Playing {query.replace('play', '').strip()} on YouTube."})

@app.route('/answer_question', methods=['POST'])
def answer():
    response = answer_questions()
    return jsonify({"response": response})


def start_talk_ai():
    """
    Start the TalkAi functionality.
    This will run the TalkAi function in a separate thread to avoid blocking the Flask server.
    """
    from threading import Thread
    query = ''
    def run_talk_ai():
        query = startListening()

# Run the Flask app
rag_pipeline = RAGPipeline()
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        try:
            print(f"Processing PDF: {filepath}", flush=True)
            rag_pipeline.run_ingestion(filepath)
            print(f"Successfully processed: {file.filename}", flush=True)
            return jsonify({"response": f"Successfully processed {file.filename}"})
        except Exception as e:
            print(f"Error processing PDF: {str(e)}", flush=True)
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

@app.route('/query_rag', methods=['POST'])
def query_rag_endpoint():
    data = request.json
    query = data.get('query', '')
    if not query:
        return jsonify({"error": "No query provided"}), 400
    response = rag_pipeline.query_rag(query)
    return jsonify({"response": response})

def check_routing_to_rag(query, chat_history):
    """
    Determine if the query is about the document using a lightweight check or LLM.
    """
    # 1. Broad heuristic first
    doc_keywords = [
        "document", "file", "pdf", "this paper", "doc", "read this", 
        "summary of the file", "what does it say", "author of the paper",
        "conclusion of the document"
    ]
    if any(k in query.lower() for k in doc_keywords):
        return True
        
    # 2. Fast LLM check for intent if vectorstore exists
    try:
        if not rag_pipeline.vectorstore:
            return False
            
        routing_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a router. Is the user asking a question about a specific document or file that they have provided or are discussing? Answer ONLY 'YES' or 'NO'."),
            MessagesPlaceholder("chat_history"),
            ("human", "{query}")
        ])
        # We use the global llm (gpt-3.5-turbo) for this fast check
        response = llm.invoke(routing_prompt.format_messages(
            query=query, 
            chat_history=chat_history[-4:] if chat_history else []
        ))
        return "YES" in response.content.upper()
    except Exception as e:
        print(f"Routing error: {e}")
        return False

@app.route('/executequery', methods=['POST'])
def execute_query():
    data = request.json
    query = data.get('query', '').lower().strip()
    history_raw = data.get('chat_history', [])
    
    # Process Chat History: Only keep last 5 exchanges to keep it efficient
    chat_history = []
    for msg in history_raw[-10:]: # 10 messages = 5 user + 5 bot
        if msg['role'] == 'user':
            chat_history.append(HumanMessage(content=msg['content']))
        else:
            chat_history.append(AIMessage(content=msg['content']))

    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    print(f"--- Processing Query: {query} ---", flush=True)
    
    # 1. PRIORITY 1: Automation/System Commands (Manual Keyword Match)
    
    # Opening apps
    if any(word in query for word in ["open calculator", "open notepad", "open this pc", "open explorer"]):
        openapp(query)
        return jsonify({"response": f"✅ Opening requested application."})
    
    # Closing apps
    if any(word in query for word in ["close calculator", "close notepad", "close this pc"]):
        closeapp(query)
        return jsonify({"response": f"✅ Closing requested application."})
    
    # Social Media
    social_keywords = ["open facebook", "open instagram", "open discord", "open whatsapp", "open youtube", "open yt"]
    if any(word in query for word in social_keywords):
        social_media(query)
        return jsonify({"response": f"✅ Opening social media."})
        
    close_social_keywords = ["close facebook", "close instagram", "close discord", "close whatsapp", "close youtube", "close yt"]
    if any(word in query for word in close_social_keywords):
        close_social(query)
        return jsonify({"response": f"✅ Closing social media."})
    
    # Music
    if query.startswith("play ") or "play song" in query:
        play_music(query)
        return jsonify({"response": f"🎶 Playing music on YouTube."})
    
    # Schedule
    if "schedule" in query or "today's plan" in query:
        schedule()
        return jsonify({"response": "📅 Reading your schedule for today."})
        
    # PC Condition
    if any(word in query for word in ["battery", "cpu usage", "system condition", "pc status", "percentage"]):
        condition()
        return jsonify({"response": "💻 Checked system conditions."})
        
    # Wish me / Time
    if any(word in query for word in ["wish me", "good morning", "good afternoon", "good evening", "date"]):
        wishme()
        return jsonify({"response": "✨ Greetings!"})

    # Research Paper (New Intent)
    if "research paper" in query or "create paper" in query or "write a paper" in query:
        response = create_research_paper(query, chat_history=chat_history)
        return jsonify({"response": response})

    # 2. PRIORITY 2: RAG Pipeline (Only if a document is relevant)
    
    # Use intelligent routing to decide if RAG should be used
    if check_routing_to_rag(query, chat_history):
        print("Routing: Decided to use RAG Pipeline", flush=True)
        rag_response = rag_pipeline.query_rag(query, chat_history=chat_history)
        
        # If RAG found useful info, return it
        if rag_response != "NO_DOCUMENTS_LOADED" and "I don't have enough information" not in rag_response:
            print("RAG: Information found in document.", flush=True)
            return jsonify({"response": f"📄 From Document: {rag_response}"})
            
        print("RAG: No relevant info found in document or RAG failed.", flush=True)

    # 3. PRIORITY 3: General AI Agent (Fallback)
    print("Using general agent for response.", flush=True)
    response = get_general_response(query, chat_history=chat_history)
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(debug=True, port=5000)  # Backend will run on port 5000