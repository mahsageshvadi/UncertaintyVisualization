import speech_recognition as sr
import time

from gtts import gTTS
from playsound import playsound



def initateSampleAudios():

	for i in range(11):

		text = "{} mm ".format(i)
		tts = gTTS(text)
		tts.save("{}_mm.mp3".format(i))


def say_uncertainty_value_every_x_second(time_intervals):
    
    if say_uncertainty_value:
        current_uncrtainty_value = random.randint(0, 10)
        playsound("{}_mm.mp3".format(current_uncrtainty_value))
        time.sleep(5)


def takeCommand():
    r=sr.Recognizer()
    microphone = sr.Microphone()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)

        command = 0
        while True:


            print("Listening...")
            audio=r.listen(source, timeout = 3)

            try:
                command=r.recognize_google(audio,language='en-in')
                print(f"user said:{command}\n")

            except Exception as e:
            		pass

            if command==0:
                    continue
        return command


def callbackWhileListening(recognizer, audio):
    try:

        print( recognizer.recognize_google(audio))
    except sr.UnknownValueError:
        print("Couldn't understand the audio")
    except sr.RequestError as e:
            pass
        
def takeCommandInBackground():
	r = sr.Recognizer()
	m = sr.Microphone()
	with m as source:
		r.adjust_for_ambient_noise(source)  
	stop_listening = r.listen_in_background(m, callbackWhileListening)
	for _ in range(50): time.sleep(0.1)
	stop_listening(wait_for_stop=False)
	while True: 
		time.sleep(0.1) 



initateSampleAudios()