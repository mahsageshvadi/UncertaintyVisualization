import speech_recognition as sr
import openai



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