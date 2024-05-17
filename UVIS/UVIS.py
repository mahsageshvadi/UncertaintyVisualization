import vtk, ctk, qt
import slicer
import numpy as np
import enum
import imp
import os

from UIVISLib.UncertaintyForegroundVisualization import UncertaintyForegroundVisualization
from UIVISLib.BackgroundModifiedVisualization import BackgroundModifiedVisualization
from UIVISLib.TexModeVisualization import TexModeVisualization
from UIVISLib.ColorLUT import ColorLUT
from UIVISLib.AudioMode import AudioMode
from UIVISLib.TumorBasedVis import TumorBasedVis
from UIVISLib.EvaluationGame import EvaluationGame
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from UIVISLib.UsefulFunctions import UsefulFunctions


class UVIS(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "UVIS"
        self.parent.categories = ["Examples"]
        self.parent.dependencies = []
        self.parent.contributors = ["Mahsa Geshvadi"]
        self.parent.helpText = """
        This module is an uncertainty visualization module which gets the uncertainty values and images and enables 
        the usert to explore different possible visualizations
        
        """
        self.parent.helpText += self.getDefaultModuleDocumentationLink()
        self.parent.acknowledgementText = """
        This file was originally developed by Mahsa Geshvadi Radiology Departmenet at Brigham and women's Hospital.
        """



class Button(enum.Enum):
    One = 1
    Two = 2
    TumorBigger = 3
    Tumor = 4
    TumorSmaller = 5


class UVISWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):

    def __init__(self, parent=None):
        self.logic = UVISLogic()
        ScriptedLoadableModuleWidget.__init__(self, parent)
        self.currentBlurinessIndex = 0
        self.current_filter_level = 0
        self.current_filter_threshold_changed = 1
        self.currentAudioThresholdValue = 40
        self.currentFlickerThresholdValue = 40
        self.input_volumes_selected_counter = 0
        self.origin = (0, 0, 0)
        self.spacing = (0.5, 0.5, 0.5)
        self.directionMatrix  = [[1, 0, 0],
                           [0, -1, 0],
                           [0, 0, -1]]

        self.input_volume_dir = None
        self.input_volume_node = None
        self.filter_levels = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

        self.red_slice_node = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed')
        self.yellow_slice_node = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeYellow')

    def onReload(self):

        packageName = 'UIVISLib'
        submoduleNames = ['UncertaintyForegroundVisualization', 'BackgroundModifiedVisualization',
                          'TexModeVisualization', 'ColorLUT', 'AudioMode', 'TumorBasedVis', 'EvaluationGame']
        for submoduleName in submoduleNames:

            f, filename, description = imp.find_module(packageName + '/' + submoduleName)
            try:
                imp.load_module(packageName + '.' + submoduleName, f, filename, description)
            finally:
                f.close()

        try:
            self.logic.game.remove_game_shortcuts()
        except:
            pass

        ScriptedLoadableModuleWidget.onReload(self)

    def on_volume_selected_from_dir(self, button_identifier):
        dialog = qt.QFileDialog()
        dialog.setFileMode(qt.QFileDialog.ExistingFile)

        if dialog.exec_():
            selectedFile = dialog.selectedFiles()[0]
            if button_identifier == 'input_volume':
                self.input_volume_selected(selectedFile)
            elif button_identifier == 'segmentation_volume':
                self.segmentation_selected(selectedFile)
            elif button_identifier == 'uncertainty_volume':
                self.uncertainty_selected(selectedFile)

    def align_volumes(self, volume_node):
         #   volume_node.SetOrigin(self.origin)
            volume_node.SetIJKToRASDirections(self.directionMatrix[0][0], self.directionMatrix[0][1], self.directionMatrix[0][2],
                                                self.directionMatrix[1][0], self.directionMatrix[1][1], self.directionMatrix[1][2],
                                                self.directionMatrix[2][0], self.directionMatrix[2][1], self.directionMatrix[2][2])

    def set_origin(self, volume_node):
            volume_node.SetOrigin(self.orifregin)

    def input_volume_selected(self, selectedFile):
        self.input_volume_node = slicer.util.loadVolume(selectedFile, properties={"show": True})
        self.input_volume_dir = selectedFile
        self.align_volumes(self.input_volume_node)

        if self.input_volume_node is not None:
            slicer.util.setSliceViewerLayers(background=self.input_volume_node)
            self.select_uncertainty_button.setVisible(True)
            self.select_uncertainty_label.setVisible(True)
            self.input_volumes_selected_counter += 1
            self.logic.input_volume_node = self.input_volume_node
            if self.input_volumes_selected_counter >= 3:
                self.all_volumes_selected()

    def segmentation_selected(self, selectedFile):
            self.segmentation_node = slicer.util.loadSegmentation(selectedFile, properties={"show": False})
            #self.set_origin(self.segmentation_node)
            if self.segmentation_node is not None:
                if self.segmentation_node.IsA('vtkMRMLSegmentationNode'):
                    self.input_volumes_selected_counter +=1
                    self.logic.segmentation_node = self.segmentation_node
                    try:
                        self.align_volumes(self.segmentation_node)
                    except:
                        pass
                else:
                    slicer.util.warningDisplay("Please select segmentation.", windowTitle="Warning")

    def uncertainty_selected(self, selectedFile):
            uncertainty_node = slicer.util.loadVolume(selectedFile,  properties={"show": False})
            self.align_volumes(uncertainty_node)
            if uncertainty_node is not None:
                self.input_volumes_selected_counter +=1
                if self.input_volumes_selected_counter >= 2:
                    self.all_volumes_selected()

            # todo it should be independednt of nifti file
            self.uncertainty_array = slicer.util.arrayFromVolume(uncertainty_node)
            self.logic.uncertaintyNode = uncertainty_node

            self.logic.uncertainty_volume_selected_initialization(self.input_volume_dir, self.score_display)

            self.slider_setup_based_on_uncertainty_value(self.color_overlay_slider_control,
                                                         self.uncertainty_array.min(),
                                                         self.uncertainty_array.max() + 1,
                                                         self.apply_initial_threshold_for_color_overlay)
            self.logic.filter_level_changed(4)
           # self.slider_setup_based_on_uncertainty_value(self.sigma_slider,
                                               #          self.filter_levels[0],
                                               #          self.filter_levels[-1],
                                                 #        self.filter_level_changed)

            self.slider_setup_based_on_uncertainty_value(self.bluriness_threshold_slider,
                                                         round(self.uncertainty_array.min()),
                                                         round(self.uncertainty_array.max()-1),
                                                         self.filter_threshold_changed,
                                                         self.current_filter_threshold_changed * 10)

            self.slider_setup_based_on_uncertainty_value(self.audio_threshold_slider,
                                                         round(self.uncertainty_array.min() * 100),
                                                         round(self.uncertainty_array.max() * 100),
                                                         self.audio_threshold_changed,
                                                         self.currentAudioThresholdValue * 10)

            self.slider_setup_based_on_uncertainty_value(self.flicker_threshold_slider,
                                                         round(self.uncertainty_array.min() * 100),
                                                         round(self.uncertainty_array.max() * 100),
                                                         self.flicker_threshold_changed,
                                                         self.currentFlickerThresholdValue * 10)

            self.cursorType.currentIndexChanged.connect(self.logic.on_cursor_changed)
            self.changeFilterType.currentIndexChanged.connect(self.on_filter_type_changed)
            slicer.util.setSliceViewerLayers(background=self.input_volume_node)

            self.red_slice_node.SetOrientation("Axial")
            self.yellow_slice_node.SetOrientation("Axial")
            self.logic.game.show_gt_in_green_view()

    def slider_setup_based_on_uncertainty_value(self, slider, min, max, value_Changed=None, value=None):

        slider.setMinimum(min)
        slider.setMaximum(max)
        if value_Changed is not None:
            slider.valueChanged.connect(value_Changed)
        if value is not None:
            slider.setValue(value)

    def select_binary_color_map(self, is_checked):
        self.logic.colorLUT.set_is_binary(is_checked)
        self.logic.colorLUT.apply_color_map()

    def open_color_picker(self, Button):
        color_dialog = qt.QColorDialog()

        color_dialog.setOption(qt.QColorDialog.ShowAlphaChannel)
        color_dialog.setOption(qt.QColorDialog.DontUseNativeDialog)

        color = color_dialog.getColor()
        h = str(color).lstrip('#')
        colorrgb = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
        print(colorrgb)

        if Button == Button.One:
            self.logic.colorLUT.set_first_color(colorrgb)
            self.logic.colorLUT.apply_color_map()

        elif Button == Button.Two:

            self.logic.colorLUT.set_second_color(colorrgb)
            self.logic.colorLUT.apply_color_map()
        else:
            self.logic.tumorBasedViS.set_color(Button, colorrgb)

    # Color overlay  functions

    def apply_candidate_color(self, first_color, second_color):
        self.logic.colorLUT.set_first_color(first_color)
        self.logic.colorLUT.apply_color_map()

        self.logic.colorLUT.set_second_color(second_color)
        self.logic.colorLUT.apply_color_map()

    def apply_initial_threshold_for_color_overlay(self, value):

        self.logic.uncertaintyForeground.apply_initial_threshold_for_color_overlay_display(value)
        self.mm_label_for_color_overlay.setText(f"{value} mm")

    def reset_colormap_selected(self):
        self.logic.colorLUT.reset_lut_togrey()
        self.color_overlay_slider_control.setValue(self.uncertainty_array.min())

    def all_volumes_selected(self):
        self.forground_uncertaintycollapsible.setVisible(True)
        self.blurinessColapsibbleButton.setVisible(True)
        self.tumorBasedCollapsible.setVisible(True)
        self.surgeonCentricCollapsible.setVisible(True)

    def game_started(self):
      #  self.game_type_label.setVisible(True)
      #  self.game_type.setVisible(True)
        self.game_leve_label.setVisible(True)
        self.game_level.setVisible(True)
        self.play_button.setVisible(True)
        self.reset_button.setVisible(False)
        self.save_button.setVisible(True)
    #    self.play_game_with_ground_truth.setVisible(True)
        self.game_stop_button.setVisible(True)
        self.modify_vis_button.setVisible(True)
        self.game_start_button.setVisible(False)

        self.tumorBasedCollapsible.setVisible(False)
        self.surgeonCentricCollapsible.setVisible(False)
        self.forground_uncertaintycollapsible.setVisible(False)
        self.blurinessColapsibbleButton.setVisible(False)
        self.collapsible_button.setVisible(False)

        self.score_label.setVisible(True)
        self.score_display.setVisible(True)

        self.logic.game.game_started()

    def game_stopped(self):

     #   self.game_type_label.setVisible(False)
      #  self.game_type.setVisible(False)
        self.game_leve_label.setVisible(False)
        self.game_level.setVisible(False)
        self.play_button.setVisible(False)
        self.play_wo_vis_button.setVisible(False)
        self.reset_button.setVisible(False)
        self.save_button.setVisible(False)
     #   self.play_game_with_ground_truth.setVisible(False)
        self.game_stop_button.setVisible(False)
        self.modify_vis_button.setVisible(False)

        self.game_start_button.setVisible(True)
        self.logic.game.game_stopped()
        self.on_game_level_changed(0)
        self.game_level.setCurrentIndex(0)

    def modify_vis(self):
        self.tumorBasedCollapsible.setVisible(True)
        self.surgeonCentricCollapsible.setVisible(True)
        self.forground_uncertaintycollapsible.setVisible(True)
        self.blurinessColapsibbleButton.setVisible(True)
        self.collapsible_button.setVisible(True)
        self.score_label.setVisible(False)
        self.score_display.setVisible(False)


    def play_game(self):
        self.reset_button.setVisible(True)
        self.tumorBasedCollapsible.setVisible(False)
        self.surgeonCentricCollapsible.setVisible(False)
        self.forground_uncertaintycollapsible.setVisible(False)
        self.blurinessColapsibbleButton.setVisible(False)
        self.collapsible_button.setVisible(False)
        self.score_label.setVisible(True)
        self.score_display.setVisible(True)

        self.logic.play_game()

    def change_model_opacity(self, Button, opacity):

        self.logic.tumorBasedViS.change_opacity_for_tumor_boundries(Button, opacity)

    # filter based functions
    def filter_level_changed(self, filter_level):

        self.current_filter_level = filter_level
        self.logic.filter_level_changed(filter_level)

    def filter_threshold_changed(self, filter_threshold):

        self.current_filter_threshold_changed = filter_threshold
        self.logic.filter_threshold_changed(filter_threshold)
        self.slider_value_label.setText(f"{filter_threshold} mm")

    def filter_mode_selected(self, in_checked):

        self.logic.current_visualization["Volume Filtering"] = True

        self.logic.is_filter_mode_selected = in_checked

        if in_checked:

            self.logic.backgroundModifiedVisualization.visualize_filtered_background()
        else:

            self.logic.backgroundModifiedVisualization.turn_blured_visualization_off()

    # surgeon centric functions
    def audio_threshold_changed(self, new_threshold):

        self.currentAudioThresholdValue = new_threshold
        self.audio_slider_value_label.setText(str(new_threshold / 100) + " mm")
        self.logic.audioMode.setThreshold(new_threshold)

    def flicker_threshold_changed(self, new_threshold):

        self.flicker_slider_value_label.setText(str(round(new_threshold / 100)) + " mm")
        self.logic.uncertaintyForeground.change_flicker_threshold(new_threshold)

    def tumor_based_mode_selected(self, in_checked):

        self.logic.current_visualization["Tumor Based"] = True
        self.logic.is_tumor_based_mode_selected = in_checked

        self.logic.tumorBasedViS.enable_tumorVIS(in_checked)

    def on_filter_type_changed(self, index):

        filterType = ""
        if index == 0:
            filterType = "Blur"
        elif index == 1:
            filterType = "Noise"
        elif index == 2:
            filterType = "Light"

        self.logic.backgroundModifiedVisualization.set_filter_type(filterType)
        self.logic.bluriness_number_of_section_changed(index=self.currentBlurinessIndex,
                                                       blurriness_intercity=self.current_filter_level / 300,
                                                       not_bluredd_uncertainty_increase=self.current_filter_threshold_changed / 100)

    def on_game_level_changed(self, index):
        self.reset_button.setVisible(False)
        if index == 2 or index == 3:
            self.play_wo_vis_button.setVisible(True)
            self.modify_vis_button.setVisible(False)
        else:
            self.play_wo_vis_button.setVisible(False)
            self.modify_vis_button.setVisible(True)


        self.logic.game_level_changed(index)

    def on_line_thickness_changed(self, Button, value):

        self.logic.tumorBasedViS.set_line_width(Button, value)

    def setup(self):

        ScriptedLoadableModuleWidget.setup(self)

        self.uiWidget = slicer.util.loadUI(self.resourcePath('UI/UVIS.ui'))
        self.layout.addWidget(self.uiWidget)

        select_input_button = self.uiWidget.findChild(qt.QPushButton, "select_Input_Volume")
        self.collapsible_button = self.uiWidget.findChild(ctk.ctkCollapsibleButton, "inputsCollapsibleButton")

        #  select_segmentation_button = self.uiWidget.findChild(qt.QPushButton, "select_segmentation")
       # self.select_segmentation_label = self.uiWidget.findChild(qt.QLabel, "Segmentation_input_label")

        self.select_uncertainty_button = self.uiWidget.findChild(qt.QPushButton, "select_Uncertainty_Volume")
        self.select_uncertainty_label = self.uiWidget.findChild(qt.QLabel, "Uncertainty_volume_Label")
        self.select_uncertainty_button.setVisible(False)
        self.select_uncertainty_label.setVisible(False)

        select_input_button.connect('clicked()', lambda: self.on_volume_selected_from_dir('input_volume'))
       # select_segmentation_button.connect('clicked()', lambda: self.on_volume_selected_from_dir('segmentation_volume'))
        self.select_uncertainty_button.connect('clicked()', lambda: self.on_volume_selected_from_dir('uncertainty_volume'))

        self.blurinessColapsibbleButton = ctk.ctkCollapsibleButton()
        self.blurinessColapsibbleButton.text = "Volume Filtering"
        self.blurinessColapsibbleButton.setVisible(False)

        self.layout.addWidget(self.blurinessColapsibbleButton)
        bluriness_collapsible_layout = qt.QFormLayout(self.blurinessColapsibbleButton)
        filter_Layout = qt.QGridLayout()
      #  bluriness_level_slider_label = qt.QLabel("Filter Level:")

      #  self.sigma_slider = qt.QSlider(qt.Qt.Horizontal)
       # self.slider_initial_setup(self.sigma_slider, self.current_filter_level)

        bluriness_l_threshold_slider = qt.QLabel("Uncertainty Threshold:")

        self.bluriness_threshold_slider = qt.QSlider(qt.Qt.Horizontal)
        self.slider_initial_setup(self.bluriness_threshold_slider, self.current_filter_threshold_changed)

        self.slider_value_label = qt.QLabel(str(self.current_filter_threshold_changed) + " mm")

        self.changeFilterType = qt.QComboBox()
        self.changeFilterType.setFixedSize(120, 30)
        self.changeFilterType.addItem("Gaussian")
        self.changeFilterType.addItem("Noise")
       # self.changeFilterType.addItem("Transparancy")
        self.changeFilterType.setCurrentIndex(0)

     #

        self.numberof_blured_sections_dropdown = qt.QComboBox()
       # self.numberof_blured_sections_dropdown.setFixedSize(100, 30)
       # for value in range(2, 12):
       #     self.numberof_blured_sections_dropdown.addItem(str(value))

      #  self.numberof_blured_sections_dropdown.addItem("Non-Binary")
      #  self.numberof_blured_sections_dropdown.setCurrentIndex(0)
        #  self.numberofBluredSectionsDropdown.currentIndexChanged.connect(self.bluriness_number_of_section_changed)

        self.select_filter_checkkbox = qt.QCheckBox("Enable")
        self.select_filter_checkkbox.toggled.connect(
            lambda: self.filter_mode_selected(self.select_filter_checkkbox.isChecked()))

      #  filter_Layout.addWidget(bluriness_level_slider_label, 1, 0)
        filter_Layout.addWidget(self.changeFilterType, 2, 2, qt.Qt.AlignRight)
      #  filter_Layout.addWidget(self.numberof_blured_sections_dropdown, 3, 2, qt.Qt.AlignRight)
        filter_Layout.addWidget(self.select_filter_checkkbox, 0, 0, qt.Qt.AlignLeft)
       # filter_Layout.addWidget(self.sigma_slider, 2, 0)
        filter_Layout.addWidget(bluriness_l_threshold_slider, 3, 0)
        slider_layout = qt.QHBoxLayout()
        slider_layout.addWidget(self.bluriness_threshold_slider)
        slider_layout.addWidget(self.slider_value_label)
        filter_Layout.addLayout(slider_layout, 4, 0)
        bluriness_collapsible_layout.addRow(filter_Layout)

        self.layout.addStretch(1)

        self.score_display = qt.QLineEdit()
        self.score_display.setReadOnly(
            True)  # Set to read-only if you only want to display the score and not allow user edits
        self.score_display.setFixedSize(200, 50)  # Increase the size of the score display
        self.score_display.setAlignment(qt.Qt.AlignCenter)
        # Add CSS styling for yellow color and larger font
        self.score_display.setStyleSheet(
            "background-color: #FFFF99; color: black; font-size: 20px; text-align: center;")

        # Add a label for the score display
        self.score_label = qt.QLabel("Score:")
        self.score_label.setFixedSize(70, 50)
        self.score_label.setStyleSheet("font-size: 20px;")  # Increase the font size

        # Create a horizontal layout for centering
        score_layout = qt.QHBoxLayout()
        score_layout.addStretch(1)
        score_layout.addWidget(self.score_label)
        score_layout.addWidget(self.score_display)
        score_layout.addStretch(1)

        # Add the horizontal layout to the main layout before "Game Evaluation"
        self.layout.addLayout(score_layout)

        self.score_label.setVisible(False)
        self.score_display.setVisible(False)

        self.tumorBasedCollapsible = ctk.ctkCollapsibleButton()
        self.tumorBasedCollapsible.text = "Tumor Based"
        self.tumorBasedCollapsible.setVisible(False)
        self.layout.addWidget(self.tumorBasedCollapsible)
        tumorBasedCollapsibleLayout = qt.QFormLayout(self.tumorBasedCollapsible)
        #  tumorBasedCollapsible.styleSheet = "color: rgb(144, 186, 136);"

        tumor_based_layout = qt.QGridLayout()

        self.select_tumorbased_checkbox = qt.QCheckBox("Enable")
        self.select_tumorbased_checkbox.toggled.connect(
            lambda: self.tumor_based_mode_selected(self.select_tumorbased_checkbox.isChecked()))

      #  self.bigger_uncertainty_slider = qt.QSlider(qt.Qt.Horizontal)
      #  self.slider_initial_setup(self.bigger_uncertainty_slider)


        self.bigger_uncertainty_slider_label = qt.QLabel("Maximum Offset: ")
      # self.opacity_label = qt.QLabel("Opacity: ")
        # self.sigma_slider.setValue(self.currentBlurinesssigma)
      #  self.bigger_uncertainty_slider.valueChanged.connect(
        #    lambda value: self.change_model_opacity(Button.TumorBigger, value))

        self.color_button_tumorbased = qt.QPushButton("Color")
        self.color_button_tumorbased.setFixedSize(50, 30)
        self.color_button_tumorbased.clicked.connect(lambda: self.open_color_picker(Button.TumorBigger))

      #  self.line_thickness_for_bigger_offset_label = qt.QLabel("Line Thickness: ")

     #   self.line_thickneess_for_bigger_offset = qt.QSpinBox()
      #  self.line_thickneess_for_bigger_offset.setRange(0, 20)
      #  self.line_thickneess_for_bigger_offset.setValue(2)
      #  self.line_thickneess_for_bigger_offset.setSingleStep(1)
      #  self.line_thickneess_for_bigger_offset.valueChanged.connect(
         #   lambda value: self.on_line_thickness_changed(Button.TumorBigger, value))

        tumor_based_layout.addWidget(self.select_tumorbased_checkbox, 0, 0)
        tumor_based_layout.addWidget(self.bigger_uncertainty_slider_label, 1, 0)
       # tumor_based_layout.addWidget(self.opacity_label, 2, 0, qt.Qt.AlignRight)
      #  tumor_based_layout.addWidget(self.bigger_uncertainty_slider, 2, 1, qt.Qt.AlignLeft)
        tumor_based_layout.addWidget(self.color_button_tumorbased, 1, 1)
      #  tumor_based_layout.addWidget(self.line_thickness_for_bigger_offset_label, 2, 3, qt.Qt.AlignRight)
    #    tumor_based_layout.addWidget(self.line_thickneess_for_bigger_offset, 2, 4, qt.Qt.AlignRight)

        self.tumor_based_uncertainty_slider = qt.QSlider(qt.Qt.Horizontal)
        self.slider_initial_setup(self.tumor_based_uncertainty_slider)

       # self.tumor_based_uncertainty_slider_label = qt.QLabel("Predicted Tumor: ")
       # self.opacity_label_tumor = qt.QLabel("Opacity: ")
      #  self.tumor_based_uncertainty_slider.valueChanged.connect(
        #    lambda value: self.change_model_opacity(Button.Tumor, value))

        # self.sigma_slider.setValue(self.currentBlurinesssigma)

   #     self.color_button_tumorbased_tumor = qt.QPushButton("Color")
      #  self.color_button_tumorbased_tumor.setFixedSize(50, 30)
      #  self.color_button_tumorbased_tumor.clicked.connect(lambda: self.open_color_picker(Button.Tumor))

     #   self.spin_box_label = qt.QLabel("Line Thickness: ")

     #   self.spin_box_tumor = qt.QSpinBox()
     #   self.spin_box_tumor.setRange(0, 20)
     #   self.spin_box_tumor.setValue(2)
     #   self.spin_box_tumor.setSingleStep(1)
     #   self.spin_box_tumor.valueChanged.connect(
       #     lambda value: self.on_line_thickness_changed(Button.Tumor, value))

      #  tumor_based_layout.addWidget(self.tumor_based_uncertainty_slider_label, 3, 0)
    #    tumor_based_layout.addWidget(self.opacity_label_tumor, 4, 0, qt.Qt.AlignRight)
   #     tumor_based_layout.addWidget(self.tumor_based_uncertainty_slider, 4, 1, qt.Qt.AlignLeft)
    #    tumor_based_layout.addWidget(self.color_button_tumorbased_tumor, 4, 2, qt.Qt.AlignRight)
    #    tumor_based_layout.addWidget(self.spin_box_label, 4, 3, qt.Qt.AlignRight)
    #    tumor_based_layout.addWidget(self.spin_box_tumor, 4, 4, qt.Qt.AlignRight)

      #  self.smaller_uncertainty_slider = qt.QSlider(qt.Qt.Horizontal)
       # self.slider_initial_setup(self.smaller_uncertainty_slider)

        self.smaller_uncertainty_slider_label = qt.QLabel("Minimum Offset:")
      # self.opacity_label_smaller = qt.QLabel("Opacity: ")
     #   self.smaller_uncertainty_slider.valueChanged.connect(
        #    lambda value: self.change_model_opacity(Button.TumorSmaller, value))

        # self.sigma_slider.setValue(self.currentBlurinesssigma)

        self.color_button_tumorbased_smaller = qt.QPushButton("Color")
        self.color_button_tumorbased_smaller.setFixedSize(50, 30)
        self.color_button_tumorbased_smaller.clicked.connect(lambda: self.open_color_picker(Button.TumorSmaller))

      #  self.spin_box_label_smaller = qt.QLabel("Line Thickness: ")

      #  self.spin_box_smaller = qt.QSpinBox()
    #    self.spin_box_smaller.setRange(0, 20)
     #   self.spin_box_smaller.setValue(2)
      #  self.spin_box_smaller.setSingleStep(1)
      #  self.spin_box_smaller.valueChanged.connect(
        #    lambda value: self.on_line_thickness_changed(Button.TumorSmaller, value))

        tumor_based_layout.addWidget(self.smaller_uncertainty_slider_label, 5, 0)
      #  tumor_based_layout.addWidget(self.opacity_label_smaller, 6, 0, qt.Qt.AlignRight)
      #  tumor_based_layout.addWidget(self.smaller_uncertainty_slider, 6, 1, qt.Qt.AlignLeft)
        tumor_based_layout.addWidget(self.color_button_tumorbased_smaller, 5, 1)
      #  tumor_based_layout.addWidget(self.spin_box_label_smaller, 6, 3, qt.Qt.AlignRight)
    #    tumor_based_layout.addWidget(self.spin_box_smaller, 6, 4, qt.Qt.AlignRight)

        tumorBasedCollapsibleLayout.addRow(tumor_based_layout)
        self.layout.addStretch(1)

        self.forground_uncertaintycollapsible = ctk.ctkCollapsibleButton()
        self.forground_uncertaintycollapsible.text = "Color Overlay"
        self.forground_uncertaintycollapsible.setVisible(False)
        self.layout.addWidget(self.forground_uncertaintycollapsible)
        forgroundUncertaintycollapsibleLayout = qt.QFormLayout(self.forground_uncertaintycollapsible)
        #    forgroundUncertaintycollapsible.styleSheet = "color: rgb(186, 136, 139);"

        self.fore_ground_vis_tabs = qt.QTabWidget()
        self.colorTab = qt.QWidget()
        self.fore_ground_vis_tabs.resize(300, 200)
        self.fore_ground_vis_tabs.addTab(self.colorTab, "Color")

        onOffVis = qt.QCheckBox("Enable")
        onOffVis.toggled.connect(lambda: self.logic.turn_visualization_off(onOffVis.isChecked()))

        self.color_candidate_1= qt.QPushButton("Color_1")
        self.color_candidate_1.setFixedSize(70, 30)
        self.color_candidate_1.clicked.connect(lambda: self.apply_candidate_color((14, 101, 20), (255, 135, 47)))

        self.color_candidate_2= qt.QPushButton("Color_2")
        self.color_candidate_2.setFixedSize(70, 30)
        self.color_candidate_2.clicked.connect(lambda: self.apply_candidate_color((75, 111, 193), (113, 33, 103)))


      #  self.color_button = qt.QPushButton("Select First Color")
     #   self.color_button.setFixedSize(130, 30)
    #    self.color_button.setFixedSize(130, 30)
    #    self.color_button.clicked.connect(lambda: self.open_color_picker(Button.One))

     #   self.color_button_2 = qt.QPushButton("Select Second Color")
     #   self.color_button_2.setFixedSize(130, 30)
     #   self.color_button_2.clicked.connect(lambda: self.open_color_picker(Button.Two))

      #  self.select_color_overlay_two_one_color = qt.QComboBox()
      #  self.select_color_overlay_two_one_color.addItem("Two Color Gradient")
      # self.select_color_overlay_two_one_color.addItem("One Color Gradient")
      #  self.select_color_overlay_two_one_color.setCurrentIndex(0)
        # self.select_color_overlay_two_one_color.currentIndexChanged.connect(self.color_overlay_two_one_changed)

        self.reset_button = qt.QPushButton("Reset")
        self.reset_button.setFixedSize(50, 30)
       # self.binary_CheckBox = qt.QCheckBox("Binary Colors")
      #  self.binary_CheckBox.toggled.connect(lambda: self.select_binary_color_map(self.binary_CheckBox.isChecked()))
        self.reset_button.connect('clicked()', self.reset_colormap_selected)

        self.color_overlay_slider_control = qt.QSlider(qt.Qt.Horizontal)
        self.slider_initial_setup(self.color_overlay_slider_control)
        self.color_overlay_slider_control.setTickPosition(qt.QSlider.TicksBelow)
        self.mm_label_for_color_overlay = qt.QLabel(str(0) + " mm")

        colort_mode_layout = qt.QGridLayout()
        colort_mode_layout.addWidget(onOffVis, 0, 0, qt.Qt.AlignLeft)
        colort_mode_layout.addWidget(self.color_candidate_1, 1, 0, qt.Qt.AlignLeft)
        colort_mode_layout.addWidget(self.color_candidate_2, 2, 0, qt.Qt.AlignLeft)
      #  colort_mode_layout.addWidget(self.select_color_overlay_two_one_color, 1, 2, qt.Qt.AlignRight)
        colort_mode_layout.addWidget(self.reset_button, 2, 2, qt.Qt.AlignRight)
    #    colort_mode_layout.addWidget(self.binary_CheckBox, 1, 2)
        slider_layout_color = qt.QHBoxLayout()
        slider_layout_color.addWidget(self.color_overlay_slider_control)
        slider_layout_color.addWidget(self.mm_label_for_color_overlay)
        colort_mode_layout.addLayout(slider_layout_color, 4, 0)
        self.colorTab.setLayout(colort_mode_layout)

        foregroundLayout = qt.QGridLayout()
        foregroundLayout.addWidget(self.fore_ground_vis_tabs, 1, 0)

        forgroundUncertaintycollapsibleLayout.addRow(foregroundLayout)

        self.layout.addStretch(1)

        self.surgeonCentricCollapsible = ctk.ctkCollapsibleButton()
        self.surgeonCentricCollapsible.text = "Surgeon Centric"
        self.surgeonCentricCollapsible.setVisible(False)
        self.layout.addWidget(self.surgeonCentricCollapsible)
        surgeonCentricCollapsibleLayout = qt.QFormLayout(self.surgeonCentricCollapsible)
        #     surgeonCentricCollapsible.styleSheet = "color: rgb(186, 163, 136)"

        self.surgoenCentricTabs = qt.QTabWidget()
        self.textModeTab = qt.QWidget()
        self.foreGroundVolumeTab = qt.QWidget()
        self.audioTab = qt.QWidget()
        self.fliCkerTab = qt.QWidget()
        self.surgoenCentricTabs.resize(300, 200)
        self.surgoenCentricTabs.addTab(self.textModeTab, "Text Mode")
        self.surgoenCentricTabs.addTab(self.foreGroundVolumeTab, "Color Overlay")
        self.surgoenCentricTabs.addTab(self.audioTab, "Audio")
        self.surgoenCentricTabs.addTab(self.fliCkerTab, "Flicker")

        self.turnOnCheckBox = qt.QCheckBox("Enable")
        self.turnOnCheckBox.toggled.connect(lambda: self.logic.text_mode_selected(self.turnOnCheckBox.isChecked()))

        self.cursorTypeText = qt.QLabel("Cursor Type:")

        self.cursorType = qt.QComboBox()
        self.cursorType.setFixedSize(130, 30)

        self.cursorType.addItem("Star Burst")
        self.cursorType.addItem("Cross 2D")
        self.cursorType.addItem("Cross Dot")
        self.cursorType.addItem("Thick Cross 2D")
        self.cursorType.addItem("Sphere")
        self.cursorType.addItem("Just Text")

        self.cursorType.setCurrentIndex(3)

        text_mode_layout = qt.QGridLayout()
        text_mode_layout.addWidget(self.turnOnCheckBox, 0, 0)
        text_mode_layout.addWidget(self.cursorTypeText, 1, 0)
        text_mode_layout.addWidget(self.cursorType, 2, 0, qt.Qt.AlignLeft)
        self.textModeTab.setLayout(text_mode_layout)

        self.surgeon_centric_checkBox = qt.QCheckBox("Enable")
        self.surgeon_centric_checkBox.toggled.connect(
            lambda: self.logic.surgeon_centric_mode_selected(self.surgeon_centric_checkBox.isChecked()))

        surgeon_centric_mode_layout = qt.QGridLayout()
        surgeon_centric_mode_layout.addWidget(self.surgeon_centric_checkBox, 0, 0, qt.Qt.AlignTop)
        self.foreGroundVolumeTab.setLayout(surgeon_centric_mode_layout)

        self.audio_checkbox = qt.QCheckBox("Enable")
        self.audio_checkbox.toggled.connect(lambda: self.logic.audio_mode_selected(self.audio_checkbox.isChecked()))

       # self.audio_dropdown = qt.QComboBox()
      #  audio_options = ["Beep 1", "Beep 2", "Don't trust"]
      #  self.audio_dropdown.setFixedSize(100, 30)
      #  self.audio_dropdown.addItems(audio_options)
      #  self.audio_dropdown.currentIndexChanged.connect(self.logic.on_audio_option_selected)

        self.audio_threshold_slider = qt.QSlider(qt.Qt.Horizontal)
        self.slider_initial_setup(self.audio_threshold_slider ,self.currentAudioThresholdValue)


        self.audio_slider_value_label = qt.QLabel(str(self.currentAudioThresholdValue / 10) + " mm")

        audioModeLayout = qt.QGridLayout()
        audioModeLayout.addWidget(self.audio_checkbox, 0, 0, qt.Qt.AlignLeft)
        audioModeLayout.addWidget(self.audio_threshold_slider, 0, 1, qt.Qt.AlignLeft)
        audioModeLayout.addWidget(self.audio_slider_value_label, 0, 2, qt.Qt.AlignLeft)
     #   audioModeLayout.addWidget(self.audio_dropdown, 1, 0, qt.Qt.AlignLeft)
        self.audioTab.setLayout(audioModeLayout)

        self.flicker_checkbox = qt.QCheckBox("Enable")
        self.flicker_checkbox.toggled.connect(lambda: self.logic.flicker_mode_selected(self.flicker_checkbox.isChecked()))

        self.flicker_threshold_slider = qt.QSlider(qt.Qt.Horizontal)
        self.flicker_threshold_slider.setFocusPolicy(qt.Qt.StrongFocus)
        self.flicker_threshold_slider.setTickInterval(10)
        self.flicker_threshold_slider.setFixedSize(200, 30)
        self.flicker_threshold_slider.setValue(self.currentFlickerThresholdValue)

        self.flicker_slider_value_label = qt.QLabel(str(round(self.currentFlickerThresholdValue / 10)) + " mm")

        flicker_mode_layout = qt.QGridLayout()
        flicker_mode_layout.addWidget(self.flicker_checkbox, 0, 0, qt.Qt.AlignTop)
        flicker_mode_layout.addWidget(self.flicker_threshold_slider, 0, 1, qt.Qt.AlignTop)
        flicker_mode_layout.addWidget(self.flicker_slider_value_label, 0, 2, qt.Qt.AlignTop)
        self.fliCkerTab.setLayout(flicker_mode_layout)

        surgeonCentricLayout = qt.QGridLayout()
        surgeonCentricLayout.addWidget(self.surgoenCentricTabs, 1, 0)

        surgeonCentricCollapsibleLayout.addRow(surgeonCentricLayout)

        self.layout.addStretch(1)

        gameCollapsibleButton = ctk.ctkCollapsibleButton()
        gameCollapsibleButton.text = "Game Evaluation"
        self.layout.addWidget(gameCollapsibleButton)
        gameCollapsibleLayout = qt.QFormLayout(gameCollapsibleButton)

        self.game_start_button = qt.QPushButton("Start")
        self.game_start_button.setFixedSize(50, 30)

        self.game_start_button.clicked.connect(self.game_started)

        self.play_button = qt.QPushButton("Play")
        self.play_button.setFixedSize(80, 30)
        self.play_button.clicked.connect(self.play_game)
        self.play_button.setVisible(False)

        self.play_wo_vis_button = qt.QPushButton("Trace Tumor")
        self.play_wo_vis_button.setFixedSize(80, 30)
        self.play_wo_vis_button.clicked.connect(self.logic.play_game_wo_vis)
        self.play_wo_vis_button.setVisible(False)

        self.save_button = qt.QPushButton("Save")
        self.save_button.setFixedSize(80, 30)
        self.save_button.clicked.connect(self.logic.save_data)
        self.save_button.setVisible(False)

        self.reset_button = qt.QPushButton("Reset")
        self.reset_button.setFixedSize(80, 30)
        self.reset_button.clicked.connect(self.logic.reset)  # Connect to your reset_game function
        self.reset_button.setVisible(False)

        self.game_stop_button = qt.QPushButton("New user")
        self.game_stop_button.setFixedSize(100, 30)
        self.game_stop_button.setVisible(False)
        self.game_stop_button.clicked.connect(self.game_stopped)

        self.modify_vis_button = qt.QPushButton("Modify Visualization")
        self.modify_vis_button.setFixedSize(140, 30)
        self.modify_vis_button.setVisible(False)
        self.modify_vis_button.clicked.connect(self.modify_vis)


        self.game_leve_label = qt.QLabel("Select Level:")
        self.game_leve_label.setFixedSize(120, 30)
        self.game_leve_label.setVisible(False)

        self.game_level = qt.QComboBox()
        self.game_level.setFixedSize(40, 30)
        self.game_level.addItem("1")
        self.game_level.addItem("2")
        self.game_level.addItem("3")
        self.game_level.addItem("4")
        self.game_level.setCurrentIndex(0)
        self.game_level.setVisible(False)

        self.game_level.currentIndexChanged.connect(self.on_game_level_changed)

        gameLayout = qt.QGridLayout()
        gameLayout.addWidget(self.game_start_button, 0, 0)
      #  gameLayout.addWidget(self.game_type_label, 1, 0)
      #  gameLayout.addWidget(self.game_type, 1, 3)
        gameLayout.addWidget(self.game_leve_label, 2, 0)
        gameLayout.addWidget(self.game_level, 2, 1)
    #    gameLayout.addWidget(self.play_game_with_ground_truth, 3, 0)
        gameLayout.addWidget(self.play_wo_vis_button, 4, 0)
        gameLayout.addWidget(self.play_button, 4, 1)
        gameLayout.addWidget(self.reset_button, 5, 0)
        #   gameLayout.addWidget(self.colorOverlay_checkBox, 2, 0)
        #    gameLayout.addWidget(self.textMode_checkBox, 3, 0)
        #    gameLayout.addWidget(self.audioMode_checkBox, 4, 0)
        gameLayout.addWidget(self.save_button, 5, 1)
        gameLayout.addWidget(self.game_stop_button, 5, 6)
        gameLayout.addWidget(self.modify_vis_button, 5, 8)


        gameCollapsibleLayout.addRow(gameLayout)




    def slider_initial_setup(self, slider, value = None,  tick_interval= 10, fixed_size_1 = 200, fixed_size_2 = 30) :

        slider.setFocusPolicy(qt.Qt.StrongFocus)
        slider.setTickInterval(tick_interval)
        slider.setFixedSize(fixed_size_1, fixed_size_2)
        if value is not None:
            slider.setValue(value)


class UVISLogic(ScriptedLoadableModuleLogic):

    def __init__(self):

        ScriptedLoadableModuleLogic.__init__(self)

        #Volumes:
        self.input_volume_node = None
        self.uncertaintyNode = None
        self.segmentation_node = None


        self.markupsNode = None
        self.crosshairNode = slicer.util.getNode("Crosshair")
        self.id = None

        self.uncertaintyForeground = None
        self.text_mode_visualization = None
        self.colorLUT = None
        self.backgroundModifiedVisualization = None
        self.audioMode = None
        self.tumorBasedViS = None
        self.numberOfActiveOnMouseMoveAtts = 0
        self.is_filter_mode_selected = False
        self.is_tumor_based_mode_selected = False
        self.data_dir = '/Users/mahsa/Dropbox (Partners HealthCare)/Mahsa-Reuben/generationv2/4mm/'
        self.layoutManager = slicer.app.layoutManager()
        self.colorLogic = slicer.modules.colors.logic()
        self.red_composite_node = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceCompositeNodeRed')
        self.current_level = 0

        self.current_visualization = {
            "Volume Filtering" : False,
            "Tumor Based" : False,
            "Color Overlay": False,
            "Text Mode": False,
            "Color Overlay Surgeon Centric" : False,
            "Audio": False,
            "Flicker": False
        }

        # Link different views
        sliceCompositeNodes = slicer.util.getNodesByClass("vtkMRMLSliceCompositeNode")
        defaultSliceCompositeNode = slicer.mrmlScene.GetDefaultNodeByClass("vtkMRMLSliceCompositeNode")
        if not defaultSliceCompositeNode:
            defaultSliceCompositeNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLSliceCompositeNode")
            defaultSliceCompositeNode.UnRegister(
                None)  # CreateNodeByClass is factory method, need to unregister the result to prevent memory leaks
            slicer.mrmlScene.AddDefaultNode(defaultSliceCompositeNode)
        sliceCompositeNodes.append(defaultSliceCompositeNode)
        for sliceCompositeNode in sliceCompositeNodes:
            sliceCompositeNode.SetLinkedControl(True)

        # View in 3D
        for sliceViewName in self.layoutManager.sliceViewNames():
            controller = self.layoutManager.sliceWidget(sliceViewName).sliceController()
            controller.setSliceVisible(True)

    #  self.uncertaintyNode= slicer.util.getNode('gp_uncertainty')
    #  self.id = self.crosshairNode.AddObserver(slicer.vtkMRMLCrosshairNode.CursorPositionModifiedEvent, self.onMouseMoved)
    #  self.pointListNode = slicer.util.getNode("vtkMRMLMarkupsFiducialNode1")

    def uncertainty_volume_selected_initialization(self, input_volume_dir, score_display):

        self.uncertaintyForeground = UncertaintyForegroundVisualization(self.uncertaintyNode, self.input_volume_node)
        self.uncertaintyArray = slicer.util.arrayFromVolume(self.uncertaintyNode)
        self.text_mode_visualization = TexModeVisualization(self.uncertaintyArray)
        self.colorLUT = ColorLUT(self.uncertaintyForeground.uncertaintyVISVolumeNode)
        self.game = EvaluationGame(self.uncertaintyArray, self.data_dir, score_display)
        self.input_volume_array = slicer.util.arrayFromVolume(self.input_volume_node)

        self.backgroundModifiedVisualization = BackgroundModifiedVisualization(self.uncertaintyArray,
                                                                              self.input_volume_array, self.input_volume_node)

        self.audioMode = AudioMode(self.uncertaintyArray)
        self.tumorBasedViS = TumorBasedVis(self.uncertaintyArray , input_volume_dir, self.input_volume_node)

    def surgeon_centric_mode_selected(self, isChecked):

        self.current_visualization["Color Overlay Surgeon Centric"] = isChecked
        if isChecked:
            self.uncertaintyForeground.set_surgeon_centric_mode(isChecked)
            #  if self.colorLUT.colorTableForSurgeonCentric is not None:
            #    self.uncertaintyForeground.displayNode.SetAndObserveColorNodeID(self.colorLUT.colorTableForSurgeonCentric.GetID())

            # self.uncertaintyForeground.turnOff(True)
            if self.numberOfActiveOnMouseMoveAtts == 0:
                self.id = self.crosshairNode.AddObserver(slicer.vtkMRMLCrosshairNode.CursorPositionModifiedEvent,
                                                         self.on_mouse_moved)
            self.numberOfActiveOnMouseMoveAtts += 1
        else:

            self.numberOfActiveOnMouseMoveAtts -= 1
            if self.numberOfActiveOnMouseMoveAtts == 0:
                self.crosshairNode.RemoveObserver(self.id)

            self.uncertaintyForeground.set_surgeon_centric_mode(isChecked)

            self.uncertaintyForeground.visualize()

    def turn_visualization_off(self, isChecked):

        self.current_visualization['Color Overlay'] = isChecked
        self.uncertaintyForeground.enable_color_overlay_foreground(isChecked)
      #  self.colorLogic.AddDefaultColorLegendDisplayNode(self.uncertaintyForeground)
      #  self.colorLogic.GetColorLegendDisplayNode(self.uncertaintyForeground).SetSize(0.1, 0.5)
      #  self.colorLogic.GetColorLegendDisplayNode(self.uncertaintyForeground).SetTitleText("")
        self.colorLUT.apply_color_map()

    def flicker_mode_selected(self, isChecked):

        self.current_visualization["Flicker"] = isChecked
        self.uncertaintyForeground.enable_disable_flicker_mode(isChecked)
        if isChecked:
            if self.numberOfActiveOnMouseMoveAtts == 0:
                self.id = self.crosshairNode.AddObserver(slicer.vtkMRMLCrosshairNode.CursorPositionModifiedEvent,
                                                         self.on_mouse_moved)
            self.numberOfActiveOnMouseMoveAtts += 1

        else:
            self.numberOfActiveOnMouseMoveAtts -= 1

            if self.numberOfActiveOnMouseMoveAtts == 0:
                self.crosshairNode.RemoveObserver(self.id)

    def text_mode_selected(self, in_checked):

        self.current_visualization['Text Mode'] = in_checked
        self.text_mode_visualization.show_markup(in_checked)

        if in_checked:
            if self.numberOfActiveOnMouseMoveAtts == 0:
                self.id = self.crosshairNode.AddObserver(slicer.vtkMRMLCrosshairNode.CursorPositionModifiedEvent,
                                                         self.on_mouse_moved)
            self.numberOfActiveOnMouseMoveAtts += 1

        else:
            self.numberOfActiveOnMouseMoveAtts -= 1

            if self.numberOfActiveOnMouseMoveAtts == 0:
                self.crosshairNode.RemoveObserver(self.id)

    def audio_mode_selected(self, is_checked):

        self.current_visualization["Audio"] = is_checked
        self.audioMode.turnOnAudioMode(is_checked)

        if is_checked:

            if self.numberOfActiveOnMouseMoveAtts == 0:
                self.id = self.crosshairNode.AddObserver(slicer.vtkMRMLCrosshairNode.CursorPositionModifiedEvent,
                                                         self.on_mouse_moved)
            self.numberOfActiveOnMouseMoveAtts += 1

        else:

            self.numberOfActiveOnMouseMoveAtts -= 1
            if self.numberOfActiveOnMouseMoveAtts == 0:
                self.crosshairNode.RemoveObserver(self.id)
        self.on_audio_option_selected(2)

    # def flickerModeSelected(self, isChecked):

    #    if isChecked:

    #      self.uncertaintyForeground.startFlicker()
    #   else:
    #          self.uncertaintyForeground.stopFlicker()

    def on_audio_option_selected(self, index):

        self.audioMode.setAudioFile(index)

    def on_cursor_changed(self, index):

        if index == 4 or index == 5:
            index += 1

        self.text_mode_visualization.change_glyph_type(index + 1)

    def bluriness_number_of_section_changed(self, index, blurriness_intercity=1, not_bluredd_uncertainty_increase=0):

        current_number_of_sections = index + 2
        sigmas = []
        uncertainty_borders = []
        test = []
        uncertainty_range = self.uncertaintyArray.max() - self.uncertaintyArray.min()
        uncertainty_sections_value = uncertainty_range / current_number_of_sections
        uncertainty_range_with_not_blured_increased = uncertainty_range - not_bluredd_uncertainty_increase
        uncertainty_sections_value_with_not_blured_increased = uncertainty_range_with_not_blured_increased / (
                current_number_of_sections - 1)

        for i in range(current_number_of_sections):

            sigmas.append(i * uncertainty_sections_value * blurriness_intercity)

            if i != current_number_of_sections:
                if i == 0:
                    uncertainty_borders.append(self.uncertaintyArray.min())
                else:
                    uncertainty_borders.append(
                        not_bluredd_uncertainty_increase + uncertainty_sections_value_with_not_blured_increased * (
                                    i - 1))

        uncertainty_borders.append(self.uncertaintyArray.max())
        self.backgroundModifiedVisualization.visualize_filtered_background(sigmas, uncertainty_borders,
                                                                           current_number_of_sections)

    def filter_level_changed(self, filter_level):
        self.backgroundModifiedVisualization.filter_level_changed(filter_level)

    def filter_threshold_changed(self, filter_threshold):
        self.backgroundModifiedVisualization.filter_threshold_changed(filter_threshold)

    def on_mouse_moved(self, observer, eventid):
        ras = [1.0, 1.0, 1.0]
        self.crosshairNode.GetCursorPositionRAS(ras)

        volumeRasToIjk = vtk.vtkMatrix4x4()
        self.uncertaintyNode.GetRASToIJKMatrix(volumeRasToIjk)

        point_Ijk = [0, 0, 0, 1]
        volumeRasToIjk.MultiplyPoint(np.append(ras, 1.0), point_Ijk)
        point_Ijk = [int(round(c)) for c in point_Ijk[0:3]]

        self.text_mode_visualization.move_markup(ras, point_Ijk)

        self.uncertaintyForeground.visualize(ras, point_Ijk)
        '''
        if self.uncertaintyForeground.is_color_overlay_surgeon_centric:
            if self.colorLUT.colorTableForSurgeonCentric is not None:
                self.uncertaintyForeground.displayNode.AutoWindowLevelOff()
                self.uncertaintyForeground.displayNode.AutoWindowLevelOn()
                self.uncertaintyForeground.displayNode.SetInterpolate(True)
                self.uncertaintyForeground.displayNode.SetAndObserveColorNodeID(
                    self.colorLUT.colorTableForSurgeonCentric.GetID())
        '''
        self.audioMode.performAudioMode(point_Ijk)

        self.uncertaintyForeground.perform_flicker_if_uncertainty_more_than_threshold(point_Ijk)

    def save_data(self):
        self.game.save_data()

    def play_game(self):

        self.game.toggle_tracing_boundary_mode(False)
        if self.current_level == 2 or self.current_level == 3:
            self.toggle_visualization(True)

        if self.is_filter_mode_selected:
            input_volume_node = self.backgroundModifiedVisualization.get_current_filtered_node()
            self.game.play(self.uncertaintyArray, input_volume_node)
        else:
            self.game.play(self.uncertaintyArray, self.input_volume_node)

    def play_game_wo_vis(self):
        self.game.toggle_tracing_boundary_mode(True)
        if self.current_level == 2 or self.current_level == 3:
            self.toggle_visualization(False)

        if self.is_filter_mode_selected:
            input_volume_node = self.backgroundModifiedVisualization.get_current_filtered_node()
            self.game.play(self.uncertaintyArray, input_volume_node)
        else:
            self.game.play(self.uncertaintyArray, self.input_volume_node)

    def reset(self):
        self.game.reset()

    def game_level_changed(self, level):

        self.current_level = level
        if self.is_filter_mode_selected:
            show_on_slicer = False
        else:
            show_on_slicer = True

        self.game.play_new_level(level)

       # self.current_data_dir = self.data_dir + case_name
     #   self.uncertaintyNode = slicer.util.loadVolume(self.current_data_dir + '/' +
                                                       # case_name + '_0_uncertainty.nii', properties={"show": show_on_slicer})
     #   self.align_volumes(self.uncertaintyNode)

        self.input_volume_node = self.game.get_input_volume_node()
        self.uncertaintyNode = self.game.get_Uncertainty_node()
        self.uncertaintyArray = self.game.get_uncertainty_array()

        self.backgroundModifiedVisualization.game_level_changes_background_modified(self.uncertaintyArray,
                                                                                    self.input_volume_node, level)
        if not self.is_filter_mode_selected:
            self.red_composite_node.SetBackgroundVolumeID(self.input_volume_node.GetID())
            current_slice = self.layoutManager.sliceWidget('Red')
            current_slice.fitSliceToBackground()
        else:
            self.backgroundModifiedVisualization.visualize_filtered_background()

        self.uncertaintyForeground.game_level_changes_uncertainty_foreground(self.uncertaintyNode, self.input_volume_node)
        self.text_mode_visualization.game_level_changes_text_mode(self.uncertaintyArray)

        self.tumorBasedViS.game_level_changes_tumor_based(self.uncertaintyArray,self.data_dir, level,  self.input_volume_node )
        if not self.is_tumor_based_mode_selected:
            self.tumorBasedViS.enable_tumorVIS(False)

        self.audioMode.game_level_changes_audio_mode(self.uncertaintyArray)

        if self.numberOfActiveOnMouseMoveAtts >0:
            self.id = self.crosshairNode.AddObserver(slicer.vtkMRMLCrosshairNode.CursorPositionModifiedEvent,
                                                         self.on_mouse_moved)

        if level == 2 or level == 3:
            self.toggle_visualization(False)
        else:
            self.toggle_visualization(True)


    def toggle_visualization(self, is_on):

        if self.current_visualization["Volume Filtering"]:
            if is_on:
                self.backgroundModifiedVisualization.visualize_filtered_background()
            else:
                self.backgroundModifiedVisualization.turn_blured_visualization_off()
        if self.current_visualization["Tumor Based"]:
            self.tumorBasedViS.enable_tumorVIS(is_on)
        if self.current_visualization["Color Overlay"]:
            self.uncertaintyForeground.enable_color_overlay_foreground(is_on)
        if self.current_visualization["Text Mode"]:
            self.text_mode_visualization.show_markup(is_on)
        if self.current_visualization["Color Overlay Surgeon Centric"]:
            self.uncertaintyForeground.set_surgeon_centric_mode(is_on)
        if self.current_visualization["Audio"]:
            self.audioMode.turnOnAudioMode(is_on)
        if self.current_visualization["Flicker"]:
            self.uncertaintyForeground.enable_disable_flicker_mode(is_on)
