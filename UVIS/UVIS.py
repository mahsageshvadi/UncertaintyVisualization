import logging
import os
import slicer
import vtk, ctk, qt
import slicer
import numpy as np
import enum
import SimpleITK as sitk
import math
import pygame
import objc
import UIVISLib
import imp


from UIVISLib.UncertaintyForegroundVisualization import UncertaintyForegroundVisualization
from UIVISLib.BackgroundModifiedVisualization import BackgroundModifiedVisualization
from UIVISLib.TexModeVisualization import TexModeVisualization
from UIVISLib.ColorLUT import ColorLUT
from UIVISLib.AudioMode import AudioMode
from UIVISLib.TumorBasedVis import TumorBasedVis
import UIVISLib.utils

from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from vtk.util import numpy_support
from AppKit import NSCursor, NSView


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

    def onReload(self):

        packageName='UIVISLib'
        submoduleNames=['UncertaintyForegroundVisualization', 'BackgroundModifiedVisualization',
                        'TexModeVisualization', 'ColorLUT', 'AudioMode', 'TumorBasedVis', 'EvaluationGame']
        for submoduleName in submoduleNames:

            f, filename, description = imp.find_module(packageName + '/' + submoduleName)
            try:
                imp.load_module(packageName+'.'+submoduleName, f, filename, description)
            finally:
                f.close()

        ScriptedLoadableModuleWidget.onReload(self)
            
    def onUncertaintyVolumeSelected(self):

        dialog = qt.QFileDialog()
        dialog.setFileMode(qt.QFileDialog.ExistingFile)

        if dialog.exec_():
            selectedFile = dialog.selectedFiles()[0]
            uncertaintyNode = slicer.util.loadVolume(selectedFile,  properties={"show":False})
            self.uncertaintyArray = slicer.util.arrayFromVolume(uncertaintyNode)
            self.logic.uncertaintyNode = uncertaintyNode
            self.logic.uncertaintyVolumeSelectedInitialization()
            
            self.x_slider.setMinimum(self.uncertaintyArray.min())
            self.x_slider.setMaximum(self.uncertaintyArray.max()+ 1)
            self.x_slider.valueChanged.connect(self.apply_threshold)

            self.sigma_slider.setMinimum(UIVISLib.utils.get_filter_levels()[0])
            self.sigma_slider.setMaximum(UIVISLib.utils.get_filter_levels()[-1])
            self.sigma_slider.valueChanged.connect(self.filter_level_changed)
            
            self.threshold_slider.setMinimum(round(self.uncertaintyArray.min()-1))
            self.threshold_slider.setMaximum(round(self.uncertaintyArray.max()-1))
            self.threshold_slider.valueChanged.connect(self.filter_threshold_changed)
            self.threshold_slider.setValue(self.current_filter_threshold_changed * 10)

            self.audio_threshold_slider.setMinimum(round(self.uncertaintyArray.min()*100))
            self.audio_threshold_slider.setMaximum(round(self.uncertaintyArray.max()*100))
            self.audio_threshold_slider.valueChanged.connect(self.audio_threshold_changed)
            self.audio_threshold_slider.setValue(self.currentAudioThresholdValue*10)
            
            self.flicker_threshold_slider.setMinimum(round(self.uncertaintyArray.min()*100))
            self.flicker_threshold_slider.setMaximum(round(self.uncertaintyArray.max()*100))
            self.flicker_threshold_slider.valueChanged.connect(self.flicker_threshold_changed)
            self.flicker_threshold_slider.setValue(self.currentFlickerThresholdValue*10)
            self.cursorType.currentIndexChanged.connect(self.logic.onCursorchanged)
            self.changeFilterType.currentIndexChanged.connect(self.onFilterChanged)


    def select_binary_color_map(self, is_checked):
        self.logic.colorLUT.setisBinary(is_checked)
        self.logic.colorLUT.applyColorMap()


    def open_color_picker(self, Button):
        color_dialog = qt.QColorDialog()

        color_dialog.setOption(qt.QColorDialog.ShowAlphaChannel)
        color_dialog.setOption(qt.QColorDialog.DontUseNativeDialog)

        color = color_dialog.getColor()
        h = str(color).lstrip('#')
        colorrgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        
        if Button == Button.One:
            self.logic.colorLUT.setFirstColor(colorrgb)
            self.logic.colorLUT.applyColorMap()
    
        elif Button == Button.Two:
        
            self.logic.colorLUT.setSecondColor(colorrgb)
            self.logic.colorLUT.applyColorMap()
        else:
            self.logic.tumorBasedViS.set_color(Button, colorrgb)
           
    def apply_threshold(self, value):

            self.logic.uncertaintyForeground.apply_threshold(value)
            self.x_slider_label.setText(f"{value} mm")

    def change_opacity(self, Button, opacity):
    
            self.logic.tumorBasedViS.change_opacity(Button, opacity)
    
    def filter_level_changed(self, filter_level):

            self.current_filter_level = filter_level
            self.logic.filter_level_changed(filter_level)

    def filter_threshold_changed(self, filter_threshold):

            self.current_filter_threshold_changed = filter_threshold
            self.logic.filter_threshold_changed(filter_threshold)
            self.slider_value_label.setText(f"{filter_threshold } mm")

    def audio_threshold_changed(self, new_threshold):
    
            self.currentAudioThresholdValue = new_threshold
            self.audio_slider_value_label.setText(str(new_threshold/100) + " mm")
            self.logic.audioMode.setThreshold(new_threshold)
            
    def flicker_threshold_changed(self, new_threshold):
    
            self.currentFlickerhresholdValue = new_threshold
            self.flicker_slider_value_label.setText(str(new_threshold/100) + " mm")
            self.logic.uncertaintyForeground.setFlickerThreshold(new_threshold)

    
  #  def bluriness_number_of_section_changed(self, index):
            
          #  self.currentBlurinessIndex = index
          #  self.logic.blurinessNumberOfSectionChanged(index = index, blurinessIntencity= self.currentBlurinesssigma/300, notBlureddUncertaintyIncrease =self.currentBlurinessBorderValue/100)
    
    def filterModeSelected(self, inChecked):

        if inChecked:
            
            self.logic.backgroundModifiedVisualization.visualizeFilteredBackground()
        else:
    
            self.logic.backgroundModifiedVisualization.turnBluredVisualizationOff()
    
    def tumorBasedModeSelected(self, inChecked):
    
            self.logic.tumorBasedViS.enable_tumorVIS(inChecked)
            
    
    def handle_combo_box(self, index):
        selected_item = self.combo_box.itemText(index)
        
        if selected_item == "Two Color Gradient":
            self.color_button_2.setVisible(True)
            self.logic.colorLUT.oneColor = False
        else:
            self.logic.colorLUT.resetColors()
            self.color_button_2.setVisible(False)
            self.logic.colorLUT.oneColor = True

    def onFilterChanged(self, index):
        
        filterType = ""
        if index == 0:
            filterType = "Blur"
        elif index == 1:
            filterType = "Noise"
        elif index == 2:
            filterType = "Light"
            
        self.logic.backgroundModifiedVisualization.setFilterType(filterType)
        self.logic.blurinessNumberOfSectionChanged(index =self.currentBlurinessIndex, blurinessIntencity=self.current_filter_level / 300, notBlureddUncertaintyIncrease =self.current_filter_threshold_changed / 100)

    def resetColormapSelected(self):
        self.logic.colorLUT.resetLUTTogrey()
        self.x_slider.setValue(self.uncertaintyArray.min())
        
    
    def on_spinbox_value_changed(self, Button, value):
                
        self.logic.tumorBasedViS.set_line_width(Button, value)
    
    



    def setup(self):

        ScriptedLoadableModuleWidget.setup(self)

        self.uiWidget = slicer.util.loadUI(self.resourcePath('UI/UVIS.ui'))
        self.layout.addWidget(self.uiWidget)

        select_uncertainty_button = self.uiWidget.findChild(qt.QPushButton, "select_Uncertainty_Volume")
        select_uncertainty_button.connect('clicked()', self.onUncertaintyVolumeSelected)


        
        blurinessColapsibbleButton = ctk.ctkCollapsibleButton()
        blurinessColapsibbleButton.text = "Volume Filtering"

        self.layout.addWidget(blurinessColapsibbleButton)
        blurinessCollapsibleLayout = qt.QFormLayout(blurinessColapsibbleButton)
        filter_Layout = qt.QGridLayout()
        blurinessLevelSliderLabel = qt.QLabel("Filter Level:")

        self.sigma_slider = qt.QSlider(qt.Qt.Horizontal)
        self.sigma_slider.setFocusPolicy(qt.Qt.StrongFocus)
        self.sigma_slider.setTickInterval(10)
        self.sigma_slider.setFixedSize(200, 30)
        self.sigma_slider.setValue(self.current_filter_level)

        blurinessLThresholdSlider = qt.QLabel("Uncertainty Threshold:")

        self.threshold_slider = qt.QSlider(qt.Qt.Horizontal)
        self.threshold_slider.setFocusPolicy(qt.Qt.StrongFocus)
        self.threshold_slider.setTickInterval(10)
        self.threshold_slider.setFixedSize(200, 30)
        self.threshold_slider.setValue(self.current_filter_threshold_changed)
        
        self.slider_value_label = qt.QLabel(str(self.current_filter_threshold_changed) + " mm")


        self.changeFilterType = qt.QComboBox()
        self.changeFilterType.setFixedSize(120, 30)
        self.changeFilterType.addItem("Guassian")
        self.changeFilterType.addItem("Noise")
        self.changeFilterType.addItem("Transparancy")
        self.changeFilterType.setCurrentIndex(0)

        
        self.numberofBluredSectionsDropdown = qt.QComboBox()
        self.numberofBluredSectionsDropdown.setFixedSize(100, 30)
        for value in range(2, 12):
            self.numberofBluredSectionsDropdown.addItem(str(value))
            
        self.numberofBluredSectionsDropdown.addItem("Non-Binary")
        self.numberofBluredSectionsDropdown.setCurrentIndex(0)
      #  self.numberofBluredSectionsDropdown.currentIndexChanged.connect(self.bluriness_number_of_section_changed)
        
        self.selectFilterCheckkBox = qt.QCheckBox("Enable")
        self.selectFilterCheckkBox.toggled.connect(lambda:self.filterModeSelected(self.selectFilterCheckkBox.isChecked()))

        filter_Layout.addWidget(blurinessLevelSliderLabel, 1, 0)
        filter_Layout.addWidget(self.changeFilterType, 2, 2, qt.Qt.AlignRight)
        filter_Layout.addWidget(self.numberofBluredSectionsDropdown, 3, 2, qt.Qt.AlignRight )
        filter_Layout.addWidget(self.selectFilterCheckkBox, 0, 0, qt.Qt.AlignLeft)
        filter_Layout.addWidget(self.sigma_slider, 2, 0)
        filter_Layout.addWidget(blurinessLThresholdSlider, 3, 0)
        slider_layout = qt.QHBoxLayout()
        slider_layout.addWidget(self.threshold_slider)
        slider_layout.addWidget(self.slider_value_label)
        filter_Layout.addLayout(slider_layout, 4, 0)
        blurinessCollapsibleLayout.addRow(filter_Layout)


        self.layout.addStretch(1)


        tumorBasedCollapsible = ctk.ctkCollapsibleButton()
        tumorBasedCollapsible.text = "Tumor Based"
        self.layout.addWidget(tumorBasedCollapsible)
        tumorBasedCollapsibleLayout = qt.QFormLayout(tumorBasedCollapsible)
      #  tumorBasedCollapsible.styleSheet = "color: rgb(144, 186, 136);"

        tumorBasedLayout = qt.QGridLayout()


        self.selectTumorbasedCheckbox = qt.QCheckBox("Enable")
        self.selectTumorbasedCheckbox.toggled.connect(lambda:self.tumorBasedModeSelected(self.selectTumorbasedCheckbox.isChecked()))
                

        self.bigger_uncertainty_slider = qt.QSlider(qt.Qt.Horizontal)
        self.bigger_uncertainty_slider.setFocusPolicy(qt.Qt.StrongFocus)
        self.bigger_uncertainty_slider.setTickInterval(10)
        self.bigger_uncertainty_slider.setFixedSize(200, 30)
        self.bigger_uncertainty_slider_label = qt.QLabel("Maximum Offset: ")
        self.opacity_label = qt.QLabel("Opacity: ")
        #self.sigma_slider.setValue(self.currentBlurinesssigma)
        self.bigger_uncertainty_slider.valueChanged.connect(lambda value: self.change_opacity(Button.TumorBigger, value))

        self.color_button_tumorbased = qt.QPushButton("Color")
        self.color_button_tumorbased.setFixedSize(50, 30)
        self.color_button_tumorbased.clicked.connect(lambda:self.open_color_picker(Button.TumorBigger))
       
       
        self.spin_box_label_bigger= qt.QLabel("Line Thickness: ")

        self.spin_box_bigger = qt.QSpinBox()
        self.spin_box_bigger.setRange(0, 20)
        self.spin_box_bigger.setValue(2)
        self.spin_box_bigger.setSingleStep(1)
        self.spin_box_bigger.valueChanged.connect(lambda value: self.on_spinbox_value_changed(Button.TumorBigger, value))

        
        tumorBasedLayout.addWidget(self.selectTumorbasedCheckbox, 0, 0)
        tumorBasedLayout.addWidget(self.bigger_uncertainty_slider_label, 1, 0)
        tumorBasedLayout.addWidget(self.opacity_label , 2, 0, qt.Qt.AlignRight)
        tumorBasedLayout.addWidget(self.bigger_uncertainty_slider, 2, 1, qt.Qt.AlignLeft)
        tumorBasedLayout.addWidget(self.color_button_tumorbased, 2, 2)
        tumorBasedLayout.addWidget(self.spin_box_label_bigger, 2, 3,qt.Qt.AlignRight)
        tumorBasedLayout.addWidget(self.spin_box_bigger, 2, 4,  qt.Qt.AlignRight)
                
        
        self.tumor_based_uncertainty_slider = qt.QSlider(qt.Qt.Horizontal)
        self.tumor_based_uncertainty_slider.setFocusPolicy(qt.Qt.StrongFocus)
        self.tumor_based_uncertainty_slider.setTickInterval(10)
        self.tumor_based_uncertainty_slider.setFixedSize(200, 30)
        self.tumor_based_uncertainty_slider_label = qt.QLabel("Predicted Tumor: ")
        self.opacity_label_tumor = qt.QLabel("Opacity: ")
        self.tumor_based_uncertainty_slider.valueChanged.connect(lambda value: self.change_opacity(Button.Tumor, value))

        #self.sigma_slider.setValue(self.currentBlurinesssigma)

        self.color_button_tumorbased_tumor = qt.QPushButton("Color")
        self.color_button_tumorbased_tumor.setFixedSize(50, 30)
        self.color_button_tumorbased_tumor.clicked.connect(lambda:self.open_color_picker(Button.Tumor))
       
        self.spin_box_label= qt.QLabel("Line Thickness: ")

        self.spin_box_tumor = qt.QSpinBox()
        self.spin_box_tumor.setRange(0, 20)
        self.spin_box_tumor.setValue(2)
        self.spin_box_tumor.setSingleStep(1)
        self.spin_box_tumor.valueChanged.connect(lambda value: self.on_spinbox_value_changed(Button.Tumor, value))

        tumorBasedLayout.addWidget(self.tumor_based_uncertainty_slider_label, 3, 0)
        tumorBasedLayout.addWidget(self.opacity_label_tumor , 4, 0, qt.Qt.AlignRight)
        tumorBasedLayout.addWidget(self.tumor_based_uncertainty_slider, 4, 1, qt.Qt.AlignLeft)
        tumorBasedLayout.addWidget(self.color_button_tumorbased_tumor, 4, 2,  qt.Qt.AlignRight)
        tumorBasedLayout.addWidget(self.spin_box_label, 4, 3,qt.Qt.AlignRight)
        tumorBasedLayout.addWidget(self.spin_box_tumor, 4, 4,  qt.Qt.AlignRight)
                
        
        
        self.smaller_uncertainty_slider = qt.QSlider(qt.Qt.Horizontal)
        self.smaller_uncertainty_slider.setFocusPolicy(qt.Qt.StrongFocus)
        self.smaller_uncertainty_slider.setTickInterval(10)
        self.smaller_uncertainty_slider.setFixedSize(200, 30)
        self.smaller_uncertainty_slider_label = qt.QLabel("Minimum Offset:")
        self.opacity_label_smaller = qt.QLabel("Opacity: ")
        self.smaller_uncertainty_slider.valueChanged.connect(lambda value: self.change_opacity(Button.TumorSmaller, value))

        #self.sigma_slider.setValue(self.currentBlurinesssigma)

        self.color_button_tumorbased_smaller = qt.QPushButton("Color")
        self.color_button_tumorbased_smaller.setFixedSize(50, 30)
        self.color_button_tumorbased_smaller.clicked.connect(lambda:self.open_color_picker(Button.TumorSmaller))

        self.spin_box_label_smaller= qt.QLabel("Line Thickness: ")

        self.spin_box_smaller = qt.QSpinBox()
        self.spin_box_smaller.setRange(0, 20)
        self.spin_box_smaller.setValue(2)
        self.spin_box_smaller.setSingleStep(1)
        self.spin_box_smaller.valueChanged.connect(lambda value: self.on_spinbox_value_changed(Button.TumorSmaller, value))

        
        tumorBasedLayout.addWidget(self.smaller_uncertainty_slider_label, 5, 0)
        tumorBasedLayout.addWidget(self.opacity_label_smaller , 6, 0, qt.Qt.AlignRight)
        tumorBasedLayout.addWidget(self.smaller_uncertainty_slider, 6, 1, qt.Qt.AlignLeft)
        tumorBasedLayout.addWidget(self.color_button_tumorbased_smaller, 6, 2,  qt.Qt.AlignRight)
        tumorBasedLayout.addWidget(self.spin_box_label_smaller, 6, 3,qt.Qt.AlignRight)
        tumorBasedLayout.addWidget(self.spin_box_smaller, 6, 4,  qt.Qt.AlignRight)
                


        tumorBasedCollapsibleLayout.addRow(tumorBasedLayout)

        self.layout.addStretch(1)



        forgroundUncertaintycollapsible = ctk.ctkCollapsibleButton()
        forgroundUncertaintycollapsible.text = "Color Overlay"
        self.layout.addWidget(forgroundUncertaintycollapsible)
        forgroundUncertaintycollapsibleLayout = qt.QFormLayout(forgroundUncertaintycollapsible)
    #    forgroundUncertaintycollapsible.styleSheet = "color: rgb(186, 136, 139);"

        self.foreGroundVISTabs = qt.QTabWidget()
        self.colorTab = qt.QWidget()
        self.foreGroundVISTabs.resize(300,200)
        self.foreGroundVISTabs.addTab(self.colorTab,"Color")

        onOffVis = qt.QCheckBox("Enable")
        onOffVis.toggled.connect(lambda:self.logic.turnVisualizationOff(onOffVis.isChecked()))


        self.color_button = qt.QPushButton("Select First Color")
        self.color_button.setFixedSize(130, 30)
        self.color_button.setFixedSize(130, 30)
        self.color_button.clicked.connect(lambda:self.open_color_picker(Button.One))


        self.color_button_2 = qt.QPushButton("Select Second Color")
        self.color_button_2.setFixedSize(130, 30)
        self.color_button_2.clicked.connect(lambda:self.open_color_picker(Button.Two))
        
        
        self.combo_box = qt.QComboBox()
        self.combo_box.addItem("Two Color Gradient")
        self.combo_box.addItem("One Color Gradient")
        self.combo_box.setCurrentIndex(0)
        self.combo_box.currentIndexChanged.connect(self.handle_combo_box)

        self.reset_button = qt.QPushButton("Reset")
        self.reset_button.setFixedSize(50, 30)
        self.binary_CheckBox = qt.QCheckBox("Binary Colors")
        self.binary_CheckBox.toggled.connect(lambda: self.select_binary_color_map(self.binary_CheckBox.isChecked()))
        self.reset_button.connect('clicked()', self.resetColormapSelected)

                
        self.x_slider = qt.QSlider(qt.Qt.Horizontal)
        self.x_slider.setFocusPolicy(qt.Qt.StrongFocus)
        self.x_slider.setTickInterval(10)
        self.x_slider.setTickPosition(qt.QSlider.TicksBelow)
        self.x_slider_label = qt.QLabel(str(0) + " mm")


        colortModeLayout = qt.QGridLayout()
        colortModeLayout.addWidget(onOffVis, 0, 0, qt.Qt.AlignLeft)
        colortModeLayout.addWidget(self.color_button, 1, 0, qt.Qt.AlignLeft)
        colortModeLayout.addWidget(self.color_button_2, 2, 0, qt.Qt.AlignLeft)
        colortModeLayout.addWidget(self.combo_box,1, 2, qt.Qt.AlignRight)
        colortModeLayout.addWidget(self.reset_button, 2, 2, qt.Qt.AlignRight)
        colortModeLayout.addWidget(self.binary_CheckBox, 1, 1)
        slider_layout_color= qt.QHBoxLayout()
        slider_layout_color.addWidget(self.x_slider)
        slider_layout_color.addWidget(self.x_slider_label)
        colortModeLayout.addLayout(slider_layout_color, 4, 0)
        self.colorTab.setLayout(colortModeLayout)

        foregroundLayout = qt.QGridLayout()
        foregroundLayout.addWidget(self.foreGroundVISTabs, 1, 0)

        forgroundUncertaintycollapsibleLayout.addRow(foregroundLayout)

        self.layout.addStretch(1)


        surgeonCentricCollapsible = ctk.ctkCollapsibleButton()
        surgeonCentricCollapsible.text = "Surgoen Centric"
        self.layout.addWidget(surgeonCentricCollapsible)
        surgeonCentricCollapsibleLayout = qt.QFormLayout(surgeonCentricCollapsible)
   #     surgeonCentricCollapsible.styleSheet = "color: rgb(186, 163, 136)"

        self.surgoenCentricTabs = qt.QTabWidget()
        self.textModeTab = qt.QWidget()
        self.foreGroundVolumeTab = qt.QWidget()
        self.audioTab = qt.QWidget()
        self.fliCkerTab = qt.QWidget()
        self.surgoenCentricTabs.resize(300,200)
        self.surgoenCentricTabs.addTab(self.textModeTab,"Text Mode")
        self.surgoenCentricTabs.addTab(self.foreGroundVolumeTab,"Color Overlay")
        self.surgoenCentricTabs.addTab(self.audioTab,"Audio")
        self.surgoenCentricTabs.addTab(self.fliCkerTab,"Flicker")
        

        self.turnOnCheckBox = qt.QCheckBox("Enable")
        self.turnOnCheckBox.toggled.connect(lambda:self.logic.textModeSelected(self.turnOnCheckBox.isChecked()))
        
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
        
        textModeLayout = qt.QGridLayout()
        textModeLayout.addWidget(self.turnOnCheckBox, 0, 0)
        textModeLayout.addWidget(self.cursorTypeText, 1, 0)
        textModeLayout.addWidget(self.cursorType, 2, 0 , qt.Qt.AlignLeft)
        self.textModeTab.setLayout(textModeLayout)

        self.surgeonCentricCheckBox = qt.QCheckBox("Enable")
        self.surgeonCentricCheckBox.toggled.connect(lambda:self.logic.surgeonCentricModeSelected(self.surgeonCentricCheckBox.isChecked()))


        surgeonCentricModeLayout = qt.QGridLayout()
        surgeonCentricModeLayout.addWidget(self.surgeonCentricCheckBox, 0, 0, qt.Qt.AlignTop )
        self.foreGroundVolumeTab.setLayout(surgeonCentricModeLayout)




        self.audioCheckbox = qt.QCheckBox("Enable")
        self.audioCheckbox.toggled.connect(lambda:self.logic.audioModeSelected(self.audioCheckbox.isChecked()))

        self.audioDropdown = qt.QComboBox()
        audio_options = ["Beep 1", "Beep 2", "Don't trust"]
        self.audioDropdown.setFixedSize(100, 30)
        self.audioDropdown.addItems(audio_options)
        self.audioDropdown.currentIndexChanged.connect(self.logic.onAudioOptionSelected)
        
        
        self.audio_threshold_slider = qt.QSlider(qt.Qt.Horizontal)
        self.audio_threshold_slider.setFocusPolicy(qt.Qt.StrongFocus)
        self.audio_threshold_slider.setTickInterval(10)
        self.audio_threshold_slider.setFixedSize(200, 30)
        self.audio_threshold_slider.setValue(self.currentAudioThresholdValue)
        
        self.audio_slider_value_label = qt.QLabel(str(self.currentAudioThresholdValue/10) + " mm")

        audioModeLayout = qt.QGridLayout()
        audioModeLayout.addWidget(self.audioCheckbox, 0, 0, qt.Qt.AlignLeft)
        audioModeLayout.addWidget(self.audio_threshold_slider, 0, 1, qt.Qt.AlignLeft)
        audioModeLayout.addWidget(self.audio_slider_value_label, 0, 2, qt.Qt.AlignLeft)
        audioModeLayout.addWidget(self.audioDropdown, 1,0, qt.Qt.AlignLeft)
        self.audioTab.setLayout(audioModeLayout)


        self.flickerCheckbox = qt.QCheckBox("Enable")
        self.flickerCheckbox.toggled.connect(lambda:self.logic.flickerModeSelected(self.flickerCheckbox.isChecked()))
        
        
        self.flicker_threshold_slider = qt.QSlider(qt.Qt.Horizontal)
        self.flicker_threshold_slider.setFocusPolicy(qt.Qt.StrongFocus)
        self.flicker_threshold_slider.setTickInterval(10)
        self.flicker_threshold_slider.setFixedSize(200, 30)
        self.flicker_threshold_slider.setValue(self.currentFlickerThresholdValue)
        
        self.flicker_slider_value_label = qt.QLabel(str(self.currentFlickerThresholdValue/10) + " mm")

        flickerModeLayout = qt.QGridLayout()
        flickerModeLayout.addWidget(self.flickerCheckbox, 0, 0, qt.Qt.AlignTop)
        flickerModeLayout.addWidget(self.flicker_threshold_slider, 0, 1, qt.Qt.AlignTop)
        flickerModeLayout.addWidget(self.flicker_slider_value_label, 0, 2, qt.Qt.AlignTop)
        self.fliCkerTab.setLayout(flickerModeLayout)


        surgeonCentricLayout = qt.QGridLayout()
        surgeonCentricLayout.addWidget(self.surgoenCentricTabs, 1, 0)

        surgeonCentricCollapsibleLayout.addRow(surgeonCentricLayout)

        self.layout.addStretch(1)

        """
        self.game = EvaluationGame()
        gameCollapsibleButton = ctk.ctkCollapsibleButton()
        gameCollapsibleButton.text = "Game"
        self.layout.addWidget(gameCollapsibleButton)
        gameCollapsibleLayout = qt.QFormLayout(gameCollapsibleButton)

        self.play_button = qt.QPushButton("Play")
        self.play_button.setFixedSize(50, 30)
        self.play_button.clicked.connect(self.game.play)  # Connect to your play_game function
        
        self.save_button = qt.QPushButton("Save")
        self.save_button.setFixedSize(50, 30)
        self.save_button.clicked.connect(self.game.save_data)

        self.reset_button = qt.QPushButton("Reset")
        self.reset_button.setFixedSize(50, 30)
        self.reset_button.clicked.connect(self.game.reset)  # Connect to your reset_game function

        self.colorOverlay_checkBox = qt.QCheckBox("Color Overlay")
        self.colorOverlay_checkBox.setFixedSize(130, 30)

        self.colorOverlay_checkBox.toggled.connect(lambda:self.game.show_colorOverlay(self.colorOverlay_checkBox.isChecked()))
        
        
        self.textMode_checkBox = qt.QCheckBox("Text Mode")
        self.textMode_checkBox.setFixedSize(130, 30)

        self.textMode_checkBox.toggled.connect(lambda:self.game.show_text(self.textMode_checkBox.isChecked()))
        
        self.audioMode_checkBox = qt.QCheckBox("Audio Mode")
        self.audioMode_checkBox.setFixedSize(130, 30)

        self.audioMode_checkBox.toggled.connect(lambda:self.game.changeAudioMode(self.audioMode_checkBox.isChecked()))
        
        
            
        gameLayout = qt.QGridLayout()
        gameLayout.addWidget(self.play_button, 0, 0)
        gameLayout.addWidget(self.reset_button, 0, 1)
        gameLayout.addWidget(self.colorOverlay_checkBox, 1, 0)
        gameLayout.addWidget(self.textMode_checkBox, 2, 0)
        gameLayout.addWidget(self.audioMode_checkBox, 3, 0)
        gameLayout.addWidget(self.save_button, 0,2)


        
        
        

        gameCollapsibleLayout.addRow(gameLayout)
"""



class UVISLogic(ScriptedLoadableModuleLogic):

    def __init__(self):

        ScriptedLoadableModuleLogic.__init__(self)
        self.markupsNode = None
        self.crosshairNode = slicer.util.getNode("Crosshair")
        self.uncertaintyNode = None
        self.id = None
        
        self.uncertaintyForeground = None
        self.markupVis = None
        self.colorLUT = None
        self.backgroundModifiedVisualization = None
        self.audioMode = None
        self.tumorBasedViS = None
        self.numberOfActiveOnMouseMoveAtts = 0
        
        # Link different views
        sliceCompositeNodes = slicer.util.getNodesByClass("vtkMRMLSliceCompositeNode")
        defaultSliceCompositeNode = slicer.mrmlScene.GetDefaultNodeByClass("vtkMRMLSliceCompositeNode")
        if not defaultSliceCompositeNode:
          defaultSliceCompositeNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLSliceCompositeNode")
          defaultSliceCompositeNode.UnRegister(None)  # CreateNodeByClass is factory method, need to unregister the result to prevent memory leaks
          slicer.mrmlScene.AddDefaultNode(defaultSliceCompositeNode)
        sliceCompositeNodes.append(defaultSliceCompositeNode)
        for sliceCompositeNode in sliceCompositeNodes:
          sliceCompositeNode.SetLinkedControl(True)
          
          
        # View in 3D
        layoutManager = slicer.app.layoutManager()
        for sliceViewName in layoutManager.sliceViewNames():
            controller = layoutManager.sliceWidget(sliceViewName).sliceController()
            controller.setSliceVisible(True)

          
          
      #  self.uncertaintyNode= slicer.util.getNode('gp_uncertainty')
      #  self.id = self.crosshairNode.AddObserver(slicer.vtkMRMLCrosshairNode.CursorPositionModifiedEvent, self.onMouseMoved)
      #  self.pointListNode = slicer.util.getNode("vtkMRMLMarkupsFiducialNode1")
        
        

    def uncertaintyVolumeSelectedInitialization(self):
    
        
        self.uncertaintyForeground = UncertaintyForegroundVisualization(self.uncertaintyNode)
        self.uncertaintyArray = slicer.util.arrayFromVolume(self.uncertaintyNode)
        self.markupVis = TexModeVisualization(self.uncertaintyArray)
        self.colorLUT = ColorLUT(self.uncertaintyForeground.uncertaintyVISVolumeNode)
        self.backgroundModifiedVisualization = BackgroundModifiedVisualization(self.uncertaintyArray)
        self.tumorBasedViS = TumorBasedVis(self.uncertaintyArray)
        self.audioMode = AudioMode(self.uncertaintyArray)
        
    def surgeonCentricModeSelected(self, isChecked):
    
        if isChecked:
            self.uncertaintyForeground.setSurgeonCentricMode(isChecked)
          #  if self.colorLUT.colorTableForSurgeonCentric is not None:
                #    self.uncertaintyForeground.displayNode.SetAndObserveColorNodeID(self.colorLUT.colorTableForSurgeonCentric.GetID())

           # self.uncertaintyForeground.turnOff(True)
            if self.numberOfActiveOnMouseMoveAtts == 0:
                self.id = self.crosshairNode.AddObserver(slicer.vtkMRMLCrosshairNode.CursorPositionModifiedEvent, self.onMouseMoved)
            self.numberOfActiveOnMouseMoveAtts +=1
        else:
            
            self.numberOfActiveOnMouseMoveAtts -=1
            if self.numberOfActiveOnMouseMoveAtts == 0:
                self.crosshairNode.RemoveObserver(self.id)
        
            self.uncertaintyForeground.setSurgeonCentricMode(isChecked)

            self.uncertaintyForeground.visualize()


    def turnVisualizationOff(self, isChecked):

            self.uncertaintyForeground.turnOff(isChecked)
            self.logic.colorLUT.applyColorMap()

    def flickerModeSelected(self, isChecked):
        
        self.uncertaintyForeground.showFlicker(isChecked)
        
        if isChecked:
            if  self.numberOfActiveOnMouseMoveAtts == 0:
                self.id = self.crosshairNode.AddObserver(slicer.vtkMRMLCrosshairNode.CursorPositionModifiedEvent, self.onMouseMoved)
            self.numberOfActiveOnMouseMoveAtts +=1

        else:
            self.numberOfActiveOnMouseMoveAtts -=1

            if self.numberOfActiveOnMouseMoveAtts == 0:
                self.crosshairNode.RemoveObserver(self.id)
                
        
    def textModeSelected(self, inChecked):
    
        self.markupVis.showMarkup(inChecked)

        if inChecked:
            if  self.numberOfActiveOnMouseMoveAtts == 0:
                self.id = self.crosshairNode.AddObserver(slicer.vtkMRMLCrosshairNode.CursorPositionModifiedEvent, self.onMouseMoved)
            self.numberOfActiveOnMouseMoveAtts +=1

        else:
            self.numberOfActiveOnMouseMoveAtts -=1

            if self.numberOfActiveOnMouseMoveAtts == 0:
                self.crosshairNode.RemoveObserver(self.id)
                

    def audioModeSelected(self, isChecked):
        
        self.audioMode.turnOnAudioMode(isChecked)

    
        if isChecked:
        
            if  self.numberOfActiveOnMouseMoveAtts == 0:
                self.id = self.crosshairNode.AddObserver(slicer.vtkMRMLCrosshairNode.CursorPositionModifiedEvent, self.onMouseMoved)
            self.numberOfActiveOnMouseMoveAtts +=1
        
        else:
        
            self.numberOfActiveOnMouseMoveAtts -=1
            if self.numberOfActiveOnMouseMoveAtts == 0:
                self.crosshairNode.RemoveObserver(self.id)
        
    
   # def flickerModeSelected(self, isChecked):
        
    #    if isChecked:
            
     #      self.uncertaintyForeground.startFlicker()
     #   else:
      #          self.uncertaintyForeground.stopFlicker()
                
                
    def onAudioOptionSelected(self, index):
    
        self.audioMode.setAudioFile(index)
    
    def onCursorchanged(self, index):
        
        if index == 4 or index == 5:
            index +=1
        
        self.markupVis.changeGlyphType(index+1)


    def blurinessNumberOfSectionChanged(self, index, blurinessIntencity=1, notBlureddUncertaintyIncrease=0):

           currentNumberofSections = index + 2
           sigmas = []
           uncertaintyBorders = []
           test = []
           uncertaintyrange = self.uncertaintyArray.max() - self.uncertaintyArray.min()
           uncertaintysectionsValue = uncertaintyrange/currentNumberofSections
           uncertaintyrangeWithNotBluredIncreased = uncertaintyrange - notBlureddUncertaintyIncrease
           uncertaintysectionsValueWithNotBluredIncreased = uncertaintyrangeWithNotBluredIncreased/(currentNumberofSections-1)

           for i in range(currentNumberofSections):

                sigmas.append(i * uncertaintysectionsValue * blurinessIntencity)

                if i != currentNumberofSections:
                        if i ==0:
                            uncertaintyBorders.append(self.uncertaintyArray.min())
                        else:
                            uncertaintyBorders.append(notBlureddUncertaintyIncrease + uncertaintysectionsValueWithNotBluredIncreased * (i-1))

           uncertaintyBorders.append(self.uncertaintyArray.max())
           self.backgroundModifiedVisualization.visualizeFilteredBackground(sigmas, uncertaintyBorders, currentNumberofSections)
    def filter_level_changed(self, filter_level):
        self.backgroundModifiedVisualization.filter_level_changed(filter_level)
    def filter_threshold_changed(self, filter_threshold):
        self.backgroundModifiedVisualization.filter_threshold_changed(filter_threshold)
    def onMouseMoved(self, observer,eventid):
        ras = [1.0, 1.0, 1.0]
        self.crosshairNode.GetCursorPositionRAS(ras)
        
        volumeRasToIjk = vtk.vtkMatrix4x4()
        self.uncertaintyNode.GetRASToIJKMatrix(volumeRasToIjk)

        point_Ijk = [0, 0, 0, 1]
        volumeRasToIjk.MultiplyPoint(np.append(ras,1.0), point_Ijk)
        point_Ijk = [ int(round(c)) for c in point_Ijk[0:3] ]
        
        self.markupVis.moveMarkup(ras, point_Ijk)

        self.uncertaintyForeground.visualize(ras, point_Ijk)
        if self.uncertaintyForeground.isSurgeonCentric:
            if self.colorLUT.colorTableForSurgeonCentric is not None:
                    
                    self.uncertaintyForeground.displayNode.AutoWindowLevelOff()
                    self.uncertaintyForeground.displayNode.AutoWindowLevelOn()
                    self.uncertaintyForeground.displayNode.SetInterpolate(True)
                    self.uncertaintyForeground.displayNode.SetAndObserveColorNodeID(self.colorLUT.colorTableForSurgeonCentric.GetID())

            
        self.audioMode.performAudioMode(point_Ijk)

        self.uncertaintyForeground.performFlicker(point_Ijk)










    
    
