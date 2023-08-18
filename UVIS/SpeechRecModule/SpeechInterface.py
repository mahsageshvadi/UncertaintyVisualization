import speech_recognition as sr
import time

from gtts import gTTS
from playsound import playsound

say_uncertainty_value = True
say_uncertainty_if_gets_bigger = True

def initateSampleAudios():

	for i in range(11):

		text_simple = "{} mm ".format(i)
		text_with_uncertainty = "{} mm uncertainty".format(i)
		tts = gTTS(text_simple)
		tts_with_uncertainty = gTTS(text_with_uncertainty)
		tts.save("{}_mm.mp3".format(i))
		tts_with_uncertainty.save("{}_mm_with_uncertainty.mp3".format(i))



def say_uncertainty_value_every_x_second(time_intervals):
    
    while say_uncertainty_value:
        current_uncrtainty_value = random.randint(0, 10)
        playsound("{}_mm.mp3".format(current_uncrtainty_value))
        time.sleep(5)


def say_uncertainty_when_gets_bigger_by_one(current_uncertainty):
    pervious_uncetainty_value = current_uncertainty
    while say_uncertainty_if_gets_bigger:
        current_uncrtainty_value = random.randint(4, 6)
        if current_uncrtainty_value - pervious_uncetainty_value != 0:
            playsound("{}_mm_with_uncertainty.mp3".format(current_uncrtainty_value))
            time.sleep(3)


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

def getPromptBasedOnCommand(command):

    prompt = f"""I have a category of 6 questions:
    Category 1: What is the uncertainty value?
    Category 2: Tell me the uncertainty value every x seconds
    Category 3: Tell me the value if it gets bigger
    Category 4: Tell me the value if it gets smaller
    Category 5: Tell me the value if it gets changed
    Category 6: Tell me where I am relative to the tumor surface

    The question below belongs to which category:
    {command}
    """



initateSampleAudios()