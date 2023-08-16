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
            audio=r.listen(source)

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

        print("Google Speech Recognition thinks you said " + recognizer.recognize_google(audio))
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))

def callbackWhileListening(recognizer, audio):
    try:

        print( recognizer.recognize_google(audio))
    except sr.UnknownValueError:
        print("Couldn't understand the audio")
    except sr.RequestError as e:
            pass
        
def takeCommandInbackground():


    r = sr.Recognizer()
    m = sr.Microphone()
    with m as source:
        r.adjust_for_ambient_noise(source)  

    top_listening = r.listen_in_background(m, callbackWhileListening)
