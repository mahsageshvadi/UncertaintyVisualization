import slicer
import numpy as np
import vtk
import cv2
import time
import os
import qt
import json
import nibabel as nib

from enum import Enum


class GameType(Enum):
    Medical_data = 1
    Abstract_data = 2


class EvaluationGame():

    def __init__(self, uncertainty_array, data_dir):

        self.game_type = None
        self.crosshairNode = slicer.util.getNode("Crosshair")

        self.ground_truth_node = None
        self.ground_truth_volume = None
        self.user_sees_node = None
        self.user_sees_volume = None
        self.uncertainty_node = None
        self.uncertainty_volume = None

        self.play_with_ground_truth = None

        self.mri_image_node = None
        self.mri_image_volume = None
        self.mri_image_volume_temp = None
        self.volume_to_save = None
        self.gt_volume = None

        self.totalScoreTextNode = None
        self.scoreTextNode = None
        self.crosshair_node_id = None
        self.initialize_scoring_texts()
        self.initialize_scoring_texts()

        self.origin = (0, 0, 0)
       # self.spacing = (0.5, 0.5, 0.5)
        self.directionMatrix  = [[1, 0, 0],
                           [0, -1, 0],
                           [0, 0, -1]]

        self.totalScore = 0
        self.player_info = {}
        self.player_username = None

        self.uncertainty_array = uncertainty_array
        self.levels = {

            '0': 'Case020',
            '1': 'Case015',
            '2': 'Case097',
            '3': 'Case112'
        }
        self.current_level = 0
        self.data_dir = data_dir

        self.gt_label_volume_node = None
        self.gt_label_volume = None
      #  self.get_ground_truth_from_dir()

        self.pred_label_volume_node = None
        self.setup_game_shortcuts()


        self.level_node_lists = []
        self.uncertainty_node_lists = []
        self.pred_label_node_list = []
        self.pred_label_volumes_list = []
        self.gt_node_lists = []
        self.gt_label_node_lists = []
        self.gt_label_volume_list = []
        self.gt_volume_lists = []
        self.load_levels()


        self.project_root = os.path.dirname(__file__)
        self.leaderboard_node = slicer.util.loadVolume(
            self.project_root +'/Art/LeaderBoard.jpeg', properties={"show": False})

        self.score_node = slicer.util.loadVolume(self.project_root +'/Art/Scoring.jpeg',
                                            properties={"show": False})

        self.green_composite_node = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceCompositeNodeGreen')
        self.yellow_composite_node = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceCompositeNodeYellow')

        self.red_composite_node = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceCompositeNodeRed')


        self.green_slice_node = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeGreen')
        self.green_slice_node.SetOrientation("Axial")

        self.yellow_slice_node = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeYellow')

        self.yellow_slice_node.SetOrientation("Axial")
        self.layoutManager = slicer.app.layoutManager()
        self.green_silce = self.layoutManager.sliceWidget('Green')
        self.red_slice = self.layoutManager.sliceWidget('Red')
        self.initialSize = 1
        self.currentSize = self.initialSize
        self.sizeIncrement = 1

        self.level_data_template = {
                "level_0": {"score": 0, "extend_of_resection": 0, "time": 0},
                "level_1": {"score": 0, "extend_of_resection": 0, "time": 0},
                "level_2": {"score": 0, "extend_of_resection": 0, "time": 0},
                "level_3": {"score": 0, "extend_of_resection": 0, "time": 0},
            }

        self.score_leaderboard_list = []
        self.username_leaderboard_list = []
        self.leader_board_data = []
        self.leader_board_init()
        self.initialize_leaderboard_for_this_level(0)
        self.current_ranking = None
        self.higher_score = 0
        self.lower_score = 0
        self.show_leader_board_data()

        self.is_tracing_boundaries = False


        # Set initial glyph size

        # self.userSeesGoldKaleVolume = slicer.util.array('UserSees_GoldKaleVolume')
        #  self.userSeesGoldKaleNode = slicer.util.getNode('UserSees_GoldKaleVolume')

        #   self.gtNode = slicer.util.getNode('GroundTruthVolume')
        #  self.gtVolume = slicer.util.array('GroundTruthVolume')
        #  self.gtMapVolume = self.gtVolume.copy()

        # self.gtMapVolume[(self.gtVolume >= 230)] = 1
        # self.gtMapVolume[(self.gtVolume <= 25)] = -1
        # self.gtMapVolume[(self.gtVolume >= 25) & (self.gtVolume <= 230)] = 0

        # self.totalScoreTextNode = slicer.util.getNode('totalScoreTextNode')
        # self.scoreTextNode = slicer.util.getNode('scoreTextNode')
        # self.UncertaintyTextNode = slicer.util.getNode('UncertaintyTextNode')

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

        self.number_of_dameges = 0
        self.VisualizationOn = False
        self.list_of_angles = []
        self.list_of_ceters = []
        self.list_of_axesLength = []
        self.list_of_variation_volumes = []
    def leader_board_init(self):

        greenViewNode = self.green_silce.mrmlSliceNode()

        for i in range(5):
            markups_node_username = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
            displayNode = markups_node_username.GetDisplayNode()
            if displayNode:
                displayNode.SetViewNodeIDs([greenViewNode.GetID()])

            markups_node_username.AddControlPoint([0, 0, 0])
            markups_node_username.SetDisplayVisibility(True)
            markups_node_username.GetDisplayNode().SetUseGlyphScale(0)
            markups_node_username.GetDisplayNode().SetGlyphType(3)
            markups_node_username.GetDisplayNode().SetSelectedColor(0, 0, 0)
            markups_node_username.GetDisplayNode().SetActiveColor(0, 0, 0)
            markups_node_username.GetDisplayNode().SetTextScale(4)
            markups_node_username.GetDisplayNode().SetGlyphType(1)
            markups_node_username.SetNthControlPointLabel(0,'')
            markups_node_username.GetDisplayNode().SetGlyphSize(0)
            markups_node_username.SetNthControlPointPosition(0, -534.520,-725.707 - 260 *i, 0.000)
            self.username_leaderboard_list.append(markups_node_username)

            markups_node_score = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
            displayNode = markups_node_score.GetDisplayNode()
            if displayNode:
                displayNode.SetViewNodeIDs([greenViewNode.GetID()])
            markups_node_score.AddControlPoint([0, 0, 0])
            markups_node_score.SetDisplayVisibility(True)
            markups_node_score.GetDisplayNode().SetUseGlyphScale(0)
            markups_node_score.GetDisplayNode().SetGlyphType(3)
            markups_node_score.GetDisplayNode().SetSelectedColor(0, 0, 0)
            markups_node_score.GetDisplayNode().SetActiveColor(0, 0, 0)
            markups_node_score.GetDisplayNode().SetTextScale(4)
            markups_node_score.GetDisplayNode().SetGlyphType(1)
            markups_node_score.SetNthControlPointLabel(0, '')
            markups_node_score.GetDisplayNode().SetGlyphSize(0)
            markups_node_score.SetNthControlPointPosition(0, -1547.677,-725.707 - 260 *i, 0.000)

            self.score_leaderboard_list.append(markups_node_score)

    def initialize_leaderboard_for_this_level(self, level):
        self.leader_board_data = []
        current_level_text = 'level_' + str(level)
        for name, data in self.player_info.items():
            self.leader_board_data.append((name, data[current_level_text]['score']))
        self.leader_board_data = sorted(self.leader_board_data, key=lambda x: x[1], reverse=True)

    def show_gt_in_green_view(self, level=0):
        self.green_composite_node.SetBackgroundVolumeID(None)
        self.yellow_composite_node.SetBackgroundVolumeID(None)
        self.green_composite_node.SetForegroundVolumeID(None)
        self.yellow_composite_node.SetForegroundVolumeID(None)

        self.green_composite_node.SetBackgroundVolumeID(self.gt_label_node_lists[level].GetID())

    def show_leader_board_data(self):
        for i in range(5):
            if i < len(self.leader_board_data) and i >= 0:
                if self.leader_board_data[i] is not None:
                    self.username_leaderboard_list[i].SetNthControlPointLabel(0, self.leader_board_data[i][0])
                    self.score_leaderboard_list[i].SetNthControlPointLabel(0, str(self.leader_board_data[i][1]))
    def update_leader_board(self):
        self.leader_board_data = sorted(self.leader_board_data, key=lambda x: x[1], reverse=True)
        self.show_leader_board_data()
        self.get_current_ranking()

    def get_current_ranking(self):
        for i, (name, score) in enumerate(self.leader_board_data):
            if name == self.player_username:
                self.current_ranking = i
        self.get_higher_lower_scores()

    def get_higher_lower_scores(self):
        if self.current_ranking == 0:
            self.higher_score = self.leader_board_data[0][1]
        else:

            self.higher_score = self.leader_board_data[self.current_ranking-1][1]

        if self.current_ranking == len(self.leader_board_data)-1:
            self.lower_score = self.leader_board_data[self.current_ranking][1]
        else:
            self.lower_score = self.leader_board_data[self.current_ranking+1][1]

    def align_volumes( self, volume_node):
         #   volume_node.SetOrigin(self.origin)
            volume_node.SetIJKToRASDirections(self.directionMatrix[0][0], self.directionMatrix[0][1], self.directionMatrix[0][2],
                                                self.directionMatrix[1][0], self.directionMatrix[1][1], self.directionMatrix[1][2],
                                                self.directionMatrix[2][0], self.directionMatrix[2][1], self.directionMatrix[2][2])

    def initialize_scoring_texts(self):

        self.totalScoreTextNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
        self.totalScoreTextNode.SetName("totalScoreTextNode")

        self.totalScoreTextNode.AddControlPoint([0, 0, 0])

        self.totalScoreTextNode.SetNthControlPointPosition(0, -603.342, -602.012, 0.000)

        self.totalScoreTextNode.GetDisplayNode().SetUseGlyphScale(0)
        self.totalScoreTextNode.GetDisplayNode().SetGlyphType(3)
        self.totalScoreTextNode.GetDisplayNode().SetSelectedColor(0, 0, 0)
        self.totalScoreTextNode.GetDisplayNode().SetActiveColor(0, 0, 0)
        self.totalScoreTextNode.GetDisplayNode().SetTextScale(3.5)
        self.totalScoreTextNode.SetNthControlPointLabel(0, "0")
        self.totalScoreTextNode.GetDisplayNode().SetGlyphSize(0)

        displayNode = self.totalScoreTextNode.GetDisplayNode()
        displayNode.SetViewNodeIDs(['vtkMRMLSliceNodeYellow'])

    def load_levels(self):

        for value in self.levels.values():

            case_name = value
            current_data_dir = self.data_dir + case_name
            input_volume_node = slicer.util.loadVolume(current_data_dir + '/' +
                                                            case_name + '_0_pred.nii',
                                                            properties={"show": False})
            self.align_volumes(input_volume_node)
            self.level_node_lists.append(input_volume_node)

            uncertaintyNode = slicer.util.loadVolume(current_data_dir + '/' +
                                                          case_name + '_0_uncertainty.nii',
                                                          properties={"show": False})
            self.align_volumes(uncertaintyNode)
            self.uncertainty_node_lists.append(uncertaintyNode)

            try:
                self.pred_label_volume_node = slicer.util.loadVolume(current_data_dir +  '/' +
                                                        case_name + '_0_pred_label.nii'
                                                                , properties={"show": False})
            except:
                self.pred_label_volume_node = slicer.util.loadVolume(current_data_dir +  '/' +
                                                        case_name + '_0_pred_label.nrrd', properties={"show": False})

            self.align_volumes(self.pred_label_volume_node)
            self.pred_label_node_list.append(self.pred_label_volume_node)
            pred_label_volume = slicer.util.arrayFromVolume(self.pred_label_volume_node)
            self.pred_label_volumes_list.append(pred_label_volume)

            gt_label_volume_node = slicer.util.loadVolume(current_data_dir +  '/' +
                                                        case_name + '_0_gt_label.nii', properties={"show": False})
            self.align_volumes(gt_label_volume_node)
            self.gt_label_node_lists.append(gt_label_volume_node)

            gt_label_volume = slicer.util.arrayFromVolume(gt_label_volume_node)
            self.gt_label_volume_list.append(gt_label_volume)

            gt_volume_node = slicer.util.loadVolume(current_data_dir +  '/' +
                                                        case_name + '_0_gt.nii', properties={"show": False})
            self.align_volumes(gt_volume_node)
            self.gt_node_lists.append(gt_volume_node)

            gt_volume = slicer.util.arrayFromVolume(gt_volume_node)
            self.gt_volume_lists.append(gt_volume)

       # self.uncertainty_array = self.uncertainty_node_lists[ee].tovolume
      #  self.gt_label_volume_node =
      #  self.gt_label_volume =
      #  self.gt_volume_node =
      #  self.gt_volume =


        self.uncertainty_node = self.uncertainty_node_lists[0]
        self.uncertainty_array = slicer.util.arrayFromVolume(self.uncertainty_node)
     #   self.input_volume_dir = input_volume_dir
        self.mri_image_node = self.level_node_lists[0]
        self.gt_label_volume_node = self.gt_label_node_lists[0]
        self.gt_label_volume = self.gt_label_volume_list[0]
        self.gt_volume_node = self.gt_node_lists[0]
        self.gt_volume = self.gt_volume_lists[0]
        self.pred_label_volume_node = self.pred_label_node_list[0]
        self.pred_label_volume = self.pred_label_volumes_list[0]

    def setup_game_shortcuts(self):

        self.play_game_shortcut = qt.QShortcut(slicer.util.mainWindow())
        self.play_game_shortcut.setKey(qt.QKeySequence('S'))
        self.play_game_shortcut.connect('activated()', lambda: self.set_gaining_score(True))


        self.stop_game_shortcut = qt.QShortcut(slicer.util.mainWindow())
        self.stop_game_shortcut.setKey(qt.QKeySequence('D'))
        self.stop_game_shortcut.connect('activated()',self.game_is_done)

    def game_is_done(self):

        nifti_img = nib.Nifti1Image(self.volume_to_save, affine=np.eye(4))

        if self.is_tracing_boundaries:
            save_file_name = '{}/GameResults/{}_{}_wo_boundary.nii'.format(self.project_root, self.player_username,
                                                                         self.current_level)
        else:
            save_file_name = '{}/GameResults/{}_{}.nii'.format(self.project_root, self.player_username,
                                                              self.current_level)
        nifti_img.to_filename(save_file_name)

        self.set_gaining_score(False)
        if self.is_tracing_boundaries:
            response = slicer.util.confirmYesNoDisplay("Are you sure you want to mark it as done?",
                                                       windowTitle="Confirm Action")
            if response:
                self.reset()



    def set_gaining_score(self, is_gaining):
        self.is_gaining_score_started = is_gaining

    def remove_game_shortcuts(self):

        self.play_game_shortcut.deleteLater()
        self.stop_game_shortcut.deleteLater()

    def get_pred_label_from_dir(self):

        self.input_volume_dir = self.input_volume_dir.replace('pred', 'pred_label')

        try:
            self.pred_label_volume_node = slicer.util.loadVolume(self.input_volume_dir, properties={"show": False})
        except:
            pred_label_dir = self.input_volume_dir.replace('nii', 'nrrd')
            self.pred_label_volume_node = slicer.util.loadVolume(pred_label_dir, properties={"show": False})

        self.pred_label_volume = slicer.util.arrayFromVolume(self.pred_label_volume_node)
        self.align_volumes(self.pred_label_volume_node)

    def align_volumes( self, volume_node):
         #   volume_node.SetSpacing(self.spacing)
          #  volume_node.SetOrigin(self.origin)
            volume_node.SetIJKToRASDirections(self.directionMatrix[0][0], self.directionMatrix[0][1], self.directionMatrix[0][2],
                                                self.directionMatrix[1][0], self.directionMatrix[1][1], self.directionMatrix[1][2],
                                                self.directionMatrix[2][0], self.directionMatrix[2][1], self.directionMatrix[2][2])

    def get_ground_truth_from_dir(self):

        gt_label_dir = self.input_volume_dir.replace('pred', 'gt_label')
        self.gt_label_volume_node = slicer.util.loadVolume(gt_label_dir, properties={"show": False})
        self.align_volumes(self.gt_label_volume_node)

        self.gt_label_volume = slicer.util.arrayFromVolume(self.gt_label_volume_node)

        gt_dir = self.input_volume_dir.replace('pred', 'gt')
        self.gt_volume_node = slicer.util.loadVolume(gt_dir, properties={"show": False})
        self.align_volumes(self.gt_volume_node)
        self.gt_volume = slicer.util.arrayFromVolume(self.gt_volume_node)

        # todo: change this
        """
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

        self.user_sees_volume_temp = self.user_sees_volume.copy()
    #    self.userSeesMapVolume = self.user_sees_volume.copy()

        self.uncertainty_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLScalarVolumeNode')
        self.uncertainty_node.SetName("Uncertainty")
        self.uncertainty_node.SetOrigin(origin)
        self.uncertainty_volume = np.zeros(shape=(self._game_volume_size, self._game_volume_size, 3), dtype=np.uint8)
        slicer.util.updateVolumeFromArray(self.uncertainty_node, self.uncertainty_volume)

        slicer.util.setSliceViewerLayers(background=self.user_sees_node)
        slicer.util.setSliceViewerLayers(foreground=None)
        self.generate_ground_truth_level_1()
"""

    def play(self, uncertainty_array, input_node):

        self.uncertainty_array = uncertainty_array
        self.mri_image_node = input_node
        self.mri_image_volume = slicer.util.arrayFromVolume(input_node)
        self.volume_to_save = np.ones(
            (self.mri_image_volume.shape[2], self.mri_image_volume.shape[1], self.mri_image_volume.shape[0]))
        self.mri_image_volume_temp = self.mri_image_volume.copy()
        self.minded_points = np.zeros(shape=(self.mri_image_volume.shape[0], self.mri_image_volume.shape[1], self.mri_image_volume.shape[2]))
        #  self.generate_user_sees(
        self.reset()
        self.crosshair_node_id = self.crosshairNode.AddObserver(slicer.vtkMRMLCrosshairNode.CursorPositionModifiedEvent,
                                                                self.on_mouse_moved)

        self.is_gaining_score_started = False
        self.are_all_the_pixels_inside_predicted_tumor = False
        self.totalScore = 0
     #   self.setup_game_scene()

    def game_stopped(self):
        with open(self.project_root +'/GameResults/player_scores.json' , 'w') as f:
            json.dump(self.player_info, f)

        slicer.mrmlScene.RemoveNode(self.ground_truth_node)
        slicer.mrmlScene.RemoveNode(self.user_sees_node)
        self.yellow_composite_node.SetBackgroundVolumeID(None)
        self.green_composite_node.SetBackgroundVolumeID(None)

    def game_started(self, text = "Enter Username:"):
        try:
            with open(self.project_root +'/GameResults/player_scores.json', 'r') as f:
                self.player_info = json.load(f)
        except:
            pass

        self.yellow_composite_node.SetBackgroundVolumeID(self.score_node.GetID())
        current_silce = self.layoutManager.sliceWidget('Yellow')
        current_silce.fitSliceToBackground()
        username = self.get_input_data(text )
        self.player_username = username
        self.add_user(self.player_username)
        self.initialize_leaderboard_for_this_level(self.current_level)
        self.get_current_ranking()

    def get_input_data(self, text):
        return qt.QInputDialog.getText(None, "Input Text", text)

    def add_user(self, username):

        if username not in self.player_info:
            user_data = {}
            for level, stats in self.level_data_template.items():
                user_data[level] = {stat: value for stat, value in stats.items()}
            self.player_info[username] = user_data
        else:
            self.game_started(f"User '{username}' already exists.")

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
        # todo
        level_one_gth = [
            {
                "angle": 0,
                "center": (150, 150),
                "axesLength": (30, 20)
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
            self.list_of_angles.append(shape['angle'])
            self.list_of_ceters.append(shape['center'])
            self.list_of_axesLength.append(shape['axesLength'])
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

        elif gtScore == 1 and userSeesScore == 1:

            return 5

    def on_mouse_moved(self, observer, eventid):

        ras = [1.0, 1.0, 1.0]
        self.crosshairNode.GetCursorPositionRAS(ras)
        volumeRasToIjk = vtk.vtkMatrix4x4()
        self.mri_image_node.GetRASToIJKMatrix(volumeRasToIjk)

        point_Ijk = [0, 0, 0, 1]
        volumeRasToIjk.MultiplyPoint(np.append(ras, 1.0), point_Ijk)
        point_Ijk = [int(round(c)) for c in point_Ijk[0:3]]
        radius = 2

        z_range = range(max(0, point_Ijk[2] - radius), min(self.mri_image_volume.shape[0], point_Ijk[2] + radius + 1))
        y_range = range(max(0, point_Ijk[1] - radius), min(self.mri_image_volume.shape[1], point_Ijk[1] + radius + 1))
        x_range = range(max(0, point_Ijk[0] - radius), min(self.mri_image_volume.shape[2], point_Ijk[0] + radius + 1))

        score = 0
        if self.is_gaining_score_started:
            for z in range(1):
                    for y in y_range:
                        for x in x_range:
                            if (x - point_Ijk[0]) ** 2 + (y - point_Ijk[1]) ** 2 + (z - point_Ijk[2]) ** 2 <= radius ** 2:
                                self.mri_image_volume[z, y, x] = self.mri_image_volume.min()
                                self.volume_to_save[x,y,z] = 0
                                # uncertainty_volume[z,y,x] = 0.0
                                if not self.minded_points[z, y, x]:
                                    self.minded_points[z, y, x] = 1
                                    temp_score = self.calculate_score_for(self.gt_label_volume[z, y, x], self.pred_label_volume[z, y, x]) / 10
                                   # if self.pred_label_volume[z, y, x] > 0:
                                     #   self.is_gaining_score_started = True
                                  #  if temp_score < 0 and self.is_gaining_score_started:
                                    #    self.scoreTextNode.GetDisplayNode().SetTextScale(5)
                                    #    self.scoreTextNode.GetDisplayNode().SetSelectedColor(1, 0, 0)
                                    #    self.scoreTextNode.GetDisplayNode().SetActiveColor(1, 0, 0)
                                  #  else:
                                    #    self.scoreTextNode.GetDisplayNode().SetTextScale(4)
                                     #   self.scoreTextNode.GetDisplayNode().SetSelectedColor(0, 0, 0)
                                    #    self.scoreTextNode.GetDisplayNode().SetActiveColor(0, 0, 0)

                                    if not self.is_tracing_boundaries:
                                        if self.is_gaining_score_started:
                                                score += temp_score
            if score < 0:
                    slicer.util.warningDisplay("You hit the healthy brain", windowTitle="Game Over")
                    self.game_is_done()
                    self.reset()
                    self.totalScore = -1

            else:
                self.totalScore += score

            if not self.is_tracing_boundaries:

                self.leader_board_data[self.current_ranking] = (self.player_username ,self.totalScore)
                if self.totalScore < self.lower_score or self.totalScore > self.higher_score:
                    self.update_leader_board()

                self.totalScoreTextNode.SetNthControlPointLabel(0,  str(round(self.totalScore)))
                self.score_leaderboard_list[self.current_ranking].SetNthControlPointLabel(0, str(round(self.totalScore)))

       #     if score > 0:
         #           self.scoreTextNode.SetNthControlPointLabel(0, "+" + str(round(score)))
         #   else:
               #     self.scoreTextNode.SetNthControlPointLabel(0, str(round(score)))

         #   self.scoreTextNode.SetNthControlPointPosition(0, ras[0], ras[1], ras[2])
            slicer.util.updateVolumeFromArray(self.mri_image_node, self.mri_image_volume)

    def calculate_score_for(self, gtScore, predScore):

        if gtScore == 0 and predScore == 0:

            return -10000

        elif gtScore == 0 and predScore == 1:

            return -100

        elif gtScore == 1 and predScore == 1:

            return 10

        elif gtScore == 1 and predScore == 0:

            return 10

            # NSCursor.hide()
    def generate_user_sees(self):
        number_of_variations = 10

        for i in range(number_of_variations):
            variations = np.zeros(shape=(300, 300, 3), dtype=np.uint8)

            angle_difference = np.random.randint(0, 30)
            angle2 = self.list_of_angles[0] + angle_difference
            center2 = (self.list_of_ceters[0][0], self.list_of_ceters[0][1] + np.random.randint(-5, 5))
            axesLength2 = self.list_of_axesLength[0]
            cv2.ellipse(variations, center2, axesLength2, angle2, 0, 360, (255, 255, 255), -1)

            angle_difference = np.random.randint(0, 30)
            angle2 = self.list_of_angles[1] + angle_difference
            center2 = (self.list_of_ceters[1][0], self.list_of_ceters[1][1] + np.random.randint(-5, 5))
            axesLength2 = self.list_of_axesLength[1]
            cv2.ellipse(variations, center2, axesLength2, angle2, 0, 360, (255, 255, 255), -1)

            angle_difference = np.random.randint(0, 30)
            angle2 = self.list_of_angles[2] + angle_difference
            center2 = (self.list_of_ceters[2][0], self.list_of_ceters[2][1] + np.random.randint(-5, 5))
            axesLength2 = self.list_of_axesLength[2]
            cv2.ellipse(variations, center2, axesLength2, angle2, 0, 360, (255, 255, 255), -1)

            angle_difference = np.random.randint(0, 30)
            angle2 = self.list_of_angles[3] + angle_difference
            center2 = (self.list_of_ceters[3][0], self.list_of_ceters[3][1] + np.random.randint(-5, 5))
            axesLength2 = self.list_of_axesLength[3]
            cv2.ellipse(variations, center2, axesLength2, angle2, 0, 360, (255, 255, 255), -1)
            slicer.util.updateVolumeFromArray(self.user_sees_node, variations)
            slicer.app.processEvents()
            time.sleep(0.2)

    def setup_game_scene(self):
        slicer.util.setSliceViewerLayers(foreground=self.user_sees_node, foregroundOpacity=1)
        defaultSliceCompositeNode = slicer.vtkMRMLSliceCompositeNode()
        defaultSliceCompositeNode.SetLinkedControl(2)
        slicer.mrmlScene.AddDefaultNode(defaultSliceCompositeNode)

    def reset(self):

        if self.crosshair_node_id is not None:
            self.crosshairNode.RemoveObserver(self.crosshair_node_id)

        self.volume_to_save = np.ones(
            (self.mri_image_volume.shape[2], self.mri_image_volume.shape[1], self.mri_image_volume.shape[0]))

        slicer.util.updateVolumeFromArray(self.mri_image_node, self.mri_image_volume_temp)
        self.mri_image_volume = self.mri_image_volume_temp.copy()
        self.totalScore = 0
        self.totalScoreTextNode.SetNthControlPointLabel(0,  str(self.totalScore))

    def show_color_overlay(self, isOn):
        if isOn:

            self.compositeNode.SetForegroundOpacity(1)

        else:
            self.compositeNode.SetForegroundOpacity(0)

        self.VisualizationOn = True

    def show_text(self, isOn):

        self.UncertaintyTextNode.SetDisplayVisibility(isOn)
        self.VisualizationOn = True

    def change_audio_mode(self, isOn):

        self.audioMode = isOn
        self.VisualizationOn = True

    def save_data(self):
        current_level_for_dict = "level_" + str(self.current_level)
        #self.player_info[self.player_username] =
        self.player_info[self.player_username][current_level_for_dict]["score"] = self.totalScore
        self.player_info[self.player_username][current_level_for_dict]["extend_of_resection"] = np.count_nonzero(self.user_sees_volume != 255)
        self.player_info[self.player_username][current_level_for_dict]["time"] = 0

        with open(self.project_root +'/GameResults/player_scores.json' , 'w') as f:
            json.dump(self.player_info, f)

    def play_new_level(self,  level):

        self.current_level = level
        self.initialize_leaderboard_for_this_level(self.current_level)
        self.show_leader_board_data()
        self.get_current_ranking()
        self.uncertainty_node = self.uncertainty_node_lists[level]
        self.uncertainty_array = slicer.util.arrayFromVolume(self.uncertainty_node_lists[level])
        self.is_gaining_score_started = False

        self.mri_image_node = self.level_node_lists[level]
        self.gt_label_volume_node = self.gt_label_node_lists[level]
        self.gt_label_volume = self.gt_label_volume_list[level]
        self.gt_volume_node = self.gt_node_lists[level]
        self.gt_volume = self.gt_volume_lists[level]
        self.pred_label_volume_node = self.pred_label_node_list[level]
        self.pred_label_volume = self.pred_label_volumes_list[level]

        self.yellow_slice_node.SetOrientation("Axial")
        self.yellow_composite_node.SetBackgroundVolumeID(self.score_node.GetID())
        current_silce = self.layoutManager.sliceWidget('Yellow')
        current_silce.fitSliceToBackground()

        self.red_composite_node.SetBackgroundVolumeID(self.mri_image_node.GetID())
        if level == 2 or level == 3:

            self.green_composite_node.SetBackgroundVolumeID(self.leaderboard_node.GetID())
            for node in slicer.util.getNodesByClass('vtkMRMLSliceCompositeNode'):
                node.SetLinkedControl(0)

        if level == 0 or level == 1:

            self.green_composite_node.SetBackgroundVolumeID(self.gt_label_volume_node.GetID())
            self.green_composite_node.SetForegroundVolumeID(self.pred_label_volume_node.GetID())
         #   self.yellow_composite_node.SetBackgroundVolumeID(None)
            self.green_composite_node.SetForegroundOpacity(0.5)

            for node in slicer.util.getNodesByClass('vtkMRMLSliceCompositeNode'):
                node.SetLinkedControl(0)

        self.green_silce.fitSliceToBackground()
        self.green_slice_node.SetOrientation("Axial")
        self.red_slice.fitSliceToBackground()

    def get_input_volume_node(self):

        return self.mri_image_node

    def get_Uncertainty_node(self):

        return self.uncertainty_node

    def get_uncertainty_array(self):

        return self.uncertainty_array

    def toggle_tracing_boundary_mode(self,tracing_mode):

        self.is_tracing_boundaries = tracing_mode

