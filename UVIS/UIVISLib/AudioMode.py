from pygame import mixer
import math
class AudioMode():

    def __init__(self, uncertaintyArray):

        self.uncertaintyArray = uncertaintyArray
        # todo: change this
        self.audioPath = "Users/mahsa/BWH/Data/"
        self.audioFileList = ["beep1.mp3", "beep2.mp3", "dontTrust.mp3"]
        self.audioFileName = "beep1.mp3"

        self.previousPosition = [-100, -100, -100]
        # Todo: check this
        self.inSafeArea = True
        self.detectedUncertaintyHigherthanThresholdPosition = None
        self.threshold = 5
        self.isOn = False
        mixer.init()
        mixer.music.load(self.audioPath + self.audioFileName)

    def setAudioFile(self, index):
        self.audioFileName = self.audioFileList[index]
        mixer.music.load(self.audioPath + self.audioFileName)

    def turnOnAudioMode(self, isChecked):

        self.isOn = isChecked

    def setThreshold(self, threshold):

        self.threshold = threshold / 100

    def performAudioMode(self, point_Ijk):

        try:
            if self.isOn:
                if self.uncertaintyArray[point_Ijk[2]][point_Ijk[1]][point_Ijk[0]] > self.threshold:
                    if self.inSafeArea:
                        self.inSafeArea = False

                        # todo: why 0.1?
                        distance = math.sqrt((self.previousPosition[0] - point_Ijk[0]) ** 2 + (
                                    self.previousPosition[1] - point_Ijk[1]) ** 2 + (
                                                         self.previousPosition[2] - point_Ijk[2]) ** 2)

                        if distance > 0.1:
                            mixer.music.play()
                        self.previousPosition = point_Ijk

                else:
                    if self.inSafeArea is not True:
                        self.inSafeArea = True
        except Exception as e:
            pass