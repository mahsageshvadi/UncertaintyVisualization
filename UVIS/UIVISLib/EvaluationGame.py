import slicer
import numpy as np
import vtk
import cv2


from enum import Enum


class GameType(Enum):
    Medical_data = 1
    Abstract_data = 2


class EvaluationGame():

    def __init__(self):

        self.game_type = None
        self.crosshairNode = slicer.util.getNode("Crosshair")

        self.ground_truth_node = None
        self.ground_truth_volume = None
        self.user_sees_node = None
        self.user_sees_volume = None
        self.uncertainty_node = None
        self.uncertainty_volume = None

        self.play_with_ground_truth = None

        # self.userSeesGoldKaleVolume = slicer.util.array('UserSees_GoldKaleVolume')
      #  self.userSeesGoldKaleNode = slicer.util.getNode('UserSees_GoldKaleVolume')

     #   self.gtNode = slicer.util.getNode('GroundTruthVolume')
      #  self.gtVolume = slicer.util.array('GroundTruthVolume')
      #  self.gtMapVolume = self.gtVolume.copy()

       # self.gtMapVolume[(self.gtVolume >= 230)] = 1
       # self.gtMapVolume[(self.gtVolume <= 25)] = -1
       # self.gtMapVolume[(self.gtVolume >= 25) & (self.gtVolume <= 230)] = 0

        self.totalScoreTextNode = slicer.util.getNode('totalScoreTextNode')
        self.scoreTextNode = slicer.util.getNode('scoreTextNode')
        self.UncertaintyTextNode = slicer.util.getNode('UncertaintyTextNode')

     #   self.uncertaintyMapNode = slicer.util.getNode('UncertaintyMapVolume')
    #    self.uncertaintyMapVolume = slicer.util.array('UncertaintyMapVolume')

     #   self.userSeesNode = slicer.util.getNode('UserSeesVolume')
     #   self.userSeesVolume = slicer.util.array('UserSeesVolume')
     #   self.userSeesMapVolume = self.userSeesVolume.copy()

      #  self.userSeesMapVolume[(self.userSeesVolume >= 230)] = 1
      #  self.userSeesMapVolume[(self.userSeesVolume <= 25)] = -1
      #  self.userSeesMapVolume[(self.userSeesVolume >= 25) & (self.userSeesVolume <= 230)] = 0
       # self.goldKaleSize = self.userSeesGoldKaleVolume.shape
      #  self.userSeesGoldKaleVolumeTemp = self.userSeesGoldKaleVolume.copy()

      #  self.uncertaintyNode = slicer.util.getNode('UncertaintyMapVolume')
      #  self.compositeNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceCompositeNodeYellow')
      #  self.compositeNode.SetForegroundVolumeID(self.uncertaintyNode.GetID())

       # self.uncertaintyArray = slicer.util.array('UncertaintyMapVolume')
      #  self.uncertaintyArray = ((self.uncertaintyArray - 0) / (255 - 0)) * (10 - 1) + 1

        # pygame.mixer.init()
        # pygame.mixer.music.load("Users/mahsa/BWH/Data/beep1.mp3")

        self.audioMode = False

        self.numberOfDameges = 0
        self.VisualizationOn = False

    def game_started(self):

        #todo: change this
        self._game_volume_size = 300

        self.ground_truth_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLScalarVolumeNode')
        self.ground_truth_node.SetName("GroundTruth")
        self.ground_truth_volume = np.zeros(shape=(self._game_volume_size, self._game_volume_size, 3), dtype=np.uint8)
        slicer.util.updateVolumeFromArray(self.ground_truth_node, self.ground_truth_volume)

        self.user_sees_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLScalarVolumeNode')
        self.user_sees_node.SetName("UserSees")
        origin = self.ground_truth_node.GetOrigin()
        self.user_sees_node.SetOrigin(origin)
        self.user_sees_volume = np.zeros(shape=(self._game_volume_size, self._game_volume_size, 3), dtype=np.uint8)
        slicer.util.updateVolumeFromArray(self.user_sees_node, self.user_sees_volume)

        self.uncertainty_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLScalarVolumeNode')
        self.uncertainty_node.SetName("Uncertainty")
        self.uncertainty_node.SetOrigin(origin)
        self.uncertainty_volume = np.zeros(shape=(self._game_volume_size, self._game_volume_size, 3), dtype=np.uint8)
        slicer.util.updateVolumeFromArray(self.uncertainty_node, self.uncertainty_volume)

        slicer.util.setSliceViewerLayers(background=self.user_sees_node)
        slicer.util.setSliceViewerLayers(foreground=None)
        self.generate_ground_truth_level_1()


    def game_stopped(self):
        slicer.mrmlScene.RemoveNode(self.ground_truth_node )
        slicer.mrmlScene.RemoveNode(self.user_sees_node )
        slicer.mrmlScene.RemoveNode(self.uncertainty_node )

    def play_with_ground_truth_checked(self, is_Checked):
        self.play_with_ground_truth = is_Checked
    def set_game_type(self, game_type):
        self.game_type = game_type

    def set_ground_truth(self):
        if self.game_type == GameType.Medical_data:
            self.calculate_ground_truth_for_medical_images()
        else:
            self.generate_ground_truth_for_abstract_game()

    def calculate_ground_truth_for_medical_images(self):
        pass

    def generate_ground_truth_for_abstract_game(self):
        pass

    def set_uncertainty(self, uncertainty_Node=None):
        if self.game_type == GameType.Medical_data:
            pass

    def calculate_uncertainty_for_generated_volumes(self):
        pass

    def generate_ground_truth_level_1(self):
        #todo
        level_one_gth = [
        {
            "angle" : 0,
            "center" : (150, 150),
            "axesLength" : (30, 20)
        },
        {
            "angle": -13,
            "center": (162, 150),
            "axesLength": (20, 36)

        },

        {
            "angle": 15,
            "center": (150, 145),
            "axesLength": (28, 25)

        },

        {
            "angle": 8,
            "center": (150, 152),
            "axesLength": (24, 28)

        }

    ]
        for shape in level_one_gth:
            self.draw_oval(self.ground_truth_volume, shape['center'], shape['axesLength'], shape['angle'])
        slicer.util.updateVolumeFromArray(self.ground_truth_node, self.ground_truth_volume)

    def draw_oval(self, image, center, axesLength, angle):

        cv2.ellipse(image, center, axesLength, angle, 0, 360, (255, 255, 255), -1)

    def calculate_score_for(self, gtScore, userSeesScore):

        if gtScore == -1 and userSeesScore == -1:

            return 0

        elif gtScore == -1 and userSeesScore == 0:

            return -500000

        elif gtScore == -1 and userSeesScore == 1:

            return -500

        elif gtScore == 0 and userSeesScore == -1:

            return 0

        elif gtScore == 0 and userSeesScore == 0:

            return 0

        elif gtScore == 0 and userSeesScore == 1:

            return 0

        elif gtScore == 1 and userSeesScore == -1:

            return 2000

        elif gtScore == 1 and userSeesScore == 0:

            return 2000
            return 2000

        elif gtScore == 1 and userSeesScore == 1:

            return 5

    def onMouseMoved(self, observer, eventid):

        ras = [1.0, 1.0, 1.0]

        self.crosshairNode.GetCursorPositionRAS(ras)
        volumeRasToIjk = vtk.vtkMatrix4x4()
        self.userSeesGoldKaleNode.GetRASToIJKMatrix(volumeRasToIjk)

        point_Ijk = [0, 0, 0, 1]
        volumeRasToIjk.MultiplyPoint(np.append(ras, 1.0), point_Ijk)
        point_Ijk = [int(round(c)) for c in point_Ijk[0:3]]
        radius = 50
        z_range = range(max(0, point_Ijk[2] - radius),
                        min(self.userSeesGoldKaleVolume.shape[0], point_Ijk[2] + radius + 1))
        y_range = range(max(0, point_Ijk[1] - radius),
                        min(self.userSeesGoldKaleVolume.shape[1], point_Ijk[1] + radius + 1))
        x_range = range(max(0, point_Ijk[0] - radius),
                        min(self.userSeesGoldKaleVolume.shape[2], point_Ijk[0] + radius + 1))

        score = 0
        for z in z_range:
            for y in y_range:
                for x in x_range:
                    if (x - point_Ijk[0]) ** 2 + (y - point_Ijk[1]) ** 2 + (z - point_Ijk[2]) ** 2 <= radius ** 2:
                        tempScore = 0
                        if not self.mindedPoints[z, y, x]:
                            self.mindedPoints[z, y, x] = 1
                            tempScore = self.calculate_score_for(self.gtMapVolume[z, y, x],
                                                                 self.userSeesMapVolume[z, y, x]) / 1000

                        if (tempScore > 0):
                            self.isGainingScoreStarted = True
                        if self.isGainingScoreStarted:
                            score += tempScore

                        self.userSeesGoldKaleVolume[z, y, x] = 255.0

        if self.uncertaintyArray[point_Ijk[2]][point_Ijk[1]][
            point_Ijk[0]] > 5 and self.isGainingScoreStarted and self.audioMode:
            pass
            # pygame.mixer.music.play()

        self.totalScore += score
        self.totalScoreTextNode.SetNthControlPointLabel(0, "$ " + str(round(self.totalScore)))
        self.UncertaintyTextNode.SetNthControlPointLabel(0, u"\u00B1 " + str(
            round(self.uncertaintyArray[point_Ijk[2]][point_Ijk[1]][point_Ijk[0]])))
        self.UncertaintyTextNode.SetNthControlPointPosition(0, ras[0], ras[1], ras[2])

        if score < 0 and self.isGainingScoreStarted:
            self.scoreTextNode.GetDisplayNode().SetTextScale(5)
            self.scoreTextNode.GetDisplayNode().SetSelectedColor(1, 0, 0)
            self.scoreTextNode.GetDisplayNode().SetActiveColor(1, 0, 0)
        else:
            self.scoreTextNode.GetDisplayNode().SetTextScale(4)
            self.scoreTextNode.GetDisplayNode().SetSelectedColor(0, 0, 0)
            self.scoreTextNode.GetDisplayNode().SetActiveColor(0, 0, 0)

        if score > 0:
            self.scoreTextNode.SetNthControlPointLabel(0, "+" + str(round(score)))
        elif score == 0:
            self.scoreTextNode.SetNthControlPointLabel(0, "")
        else:
            self.numberOfDameges += 1
            self.scoreTextNode.SetNthControlPointLabel(0, str(round(score)))

        self.scoreTextNode.SetNthControlPointPosition(0, ras[0], ras[1], ras[2])

        slicer.util.updateVolumeFromArray(self.userSeesGoldKaleNode, self.userSeesGoldKaleVolume)

    def play(self):

        self.mindedPoints = np.zeros(shape=(self.goldKaleSize[0], self.goldKaleSize[1], self.goldKaleSize[2]))
        self.crosshairNodeId = self.crosshairNode.AddObserver(slicer.vtkMRMLCrosshairNode.CursorPositionModifiedEvent,
                                                              self.onMouseMoved)
        self.isGainingScoreStarted = False
        self.totalScore = 0
        self.setupGameScene()

    # NSCursor.hide()

    def setupGameScene(self):
        slicer.util.setSliceViewerLayers(foreground=self.userSeesGoldKaleNode, foregroundOpacity=1)
        defaultSliceCompositeNode = slicer.vtkMRMLSliceCompositeNode()
        defaultSliceCompositeNode.SetLinkedControl(2)
        slicer.mrmlScene.AddDefaultNode(defaultSliceCompositeNode)

    def reset(self):

        self.crosshairNode.RemoveAllObservers()
        slicer.util.updateVolumeFromArray(self.userSeesGoldKaleNode, self.userSeesGoldKaleVolumeTemp)
        self.userSeesGoldKaleVolume = self.userSeesGoldKaleVolumeTemp.copy()
        self.totalScore = 0
        self.totalScoreTextNode.SetNthControlPointLabel(0, "$ " + str(self.totalScore))
        self.numberOfDameges = 0

    def show_colorOverlay(self, isOn):
        if isOn:

            self.compositeNode.SetForegroundOpacity(1)

        else:
            self.compositeNode.SetForegroundOpacity(0)

        self.VisualizationOn = True

    def show_text(self, isOn):

        self.UncertaintyTextNode.SetDisplayVisibility(isOn)
        self.VisualizationOn = True

    def changeAudioMode(self, isOn):

        self.audioMode = isOn
        self.VisualizationOn = True

    def save_data(self):

        data_for_save = {
            "Number Of Damages: ": self.numberOfDameges,
            "Score ": self.totalScore,
            "ExtedofResect: ": np.count_nonzero(self.userSeesGoldKaleVolume != 255),
            "VisualizationOn": self.VisualizationOn

        }
        print(data_for_save)
