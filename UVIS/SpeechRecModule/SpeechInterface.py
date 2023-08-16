import speech_recognition as sr
import time




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

takeCommand()
