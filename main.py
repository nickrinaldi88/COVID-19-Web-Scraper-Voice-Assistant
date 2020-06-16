# Create a web scraper to track realtime coronavirus statistics. Web Scraper can be accessed via voice
# assistant
import requests
import json
import pyttsx3
import speech_recognition as sr
import re
import threading
import time

API_KEY = "tFCcxP6TEDXp"
PROJECT_TOKEN = "t_nOc_0UNv0D"
RUN_TOKEN = "tZVTTg6AxYUV"

class Data:
    def __init__(self, api_key, project_token):
        self.api_key = api_key
        self.project_token = project_token
        self.params = {
            "api_key": self.api_key
        }
        self.data = self.get_data() # as instance is created, get request

    def get_data(self):
        response = requests.get("https://www.parsehub.com/api/v2/projects/{}/last_ready_run/data".format(self.project_token),
                                params={"api_key": API_KEY})
        data = json.loads(response.text)
        return data

    def get_total_cases(self):
        totals = self.data['total']
        for content in totals:
            if content['name'] == "Coronavirus Cases:":
                return content['value']

    def get_total_recovered(self):
        totals = self.data['total']
        for content in totals:
            if content['name'] == "Recovered":
                return content['value']

    def get_total_deaths(self):
        totals = self.data['total']
        for content in totals:
            if content['name'] == "Deaths:":
                return content['value']

        return "0"

    def country_data(self, country):
        countries = self.data['country']
        for content in countries:
            if content['name'].lower() == country.lower():
                return content

        return "0"

    def get_list_of_countries(self):
        countries = [country['name'].lower() for country in self.data['country']]

        return countries

    def update_data(self):
        response = requests.get("https://www.parsehub.com/api/v2/projects/{}/run".format(self.project_token),
                                params=self.params) # initialize new run on Parsehub servers

        def poll():
            time.sleep(0.1)
            old_data = self.data
            while True:
                new_data = self.get_data()
                if new_data != old_data:
                    self.data = new_data
                    print("Data updated")
                    break
                time.sleep(5)


        t = threading.Thread(target=poll)
        t.start()




def speak(text):
    engine = pyttsx3.init() # initialize engine
    engine.say(text)
    engine.runAndWait()

def get_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source: # context manager
        audio = r.listen(source)
        said = "" # will store audio from mic

    try:
        said = r.recognize_google(audio)
    except Exception as e:
        print("Exception: {}".format(str(e)))

    return said.lower()

def main():
    print("Started Program")
    data = Data(API_KEY, PROJECT_TOKEN)
    END_PHRASE = "stop"
    country_list = data.get_list_of_countries()

    TOTAL_PATTERNS = {
        re.compile("[\w\s]+ total [\w\s] + cases"):data.get_total_cases, # search for 'any num of words' total, 'any num of words' cases
        re.compile("[\w\s]+ total cases"): data.get_total_cases,
        re.compile("[\w\s]+ total [\w\s] + deaths"): data.get_total_deaths,
        re.compile("[\w\s]+ total deaths"): data.get_total_deaths,
    }

    COUNTRY_PATTERNS = {
        re.compile("[\w\s]+ cases"): lambda country: data.country_data(country)['total_cases'],
        # search for 'any num of words' total, 'any num of words' cases
        re.compile("[\w\s]+ deaths"): lambda country: data.country_data(country)['total_deaths'],
        re.compile("[\w\s]+ new deaths"): lambda country: data.country_data(country)['new_deaths']

    }

    UPDATE_COMMAND = "update"

    while True:
        print("Listening...")
        text = get_audio()
        print(text) # see what computer interprets
        result = None

        for pattern, func in COUNTRY_PATTERNS.items():
            if pattern.match(text):
                words = set(text.split(" ")) # just a set of words
                for country in country_list:
                    if country in words: # find country in set
                        result = func(country)
                        break

        for pattern, func in TOTAL_PATTERNS.items():
            if pattern.match(text):
                result = func()
                break

        if text == UPDATE_COMMAND:
            result = "Data is being updated. This may take a moment!"
            data.update_data()

        if result:
            speak(result)

        if text.find(END_PHRASE) != -1: # if it hears "stop"
            print("Exit")# stop loop
            break

main()

# Find way to record country name, and place it as argument into new_deaths() func
# Total Patterns work
        # TODO Integrate new Speech Recognition API with more accuracy