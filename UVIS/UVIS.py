import logging
import os
import slicer
import vtk, ctk, qt
import slicer
import numpy as np
import enum
import SimpleITK as sitk
import math

from scipy.ndimage import gaussian_filter
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from playsound import playsound
from vtk.util import numpy_support

# UVIS
#

class UVIS(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "UVIS"  # TODO: make this more human readable by adding spaces
        self.parent.categories = ["Examples"]  # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["Mahsa Geshvadi"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        self.parent.helpText = """
        This is a scripted loadable module bundled into the Continuous Monitoring Extension.
        It supports the tracking of surgical instruments and the construction and display of the positions
        visited by the instruments within a volume of interest.
        """
        self.parent.helpText += self.getDefaultModuleDocumentationLink()
        self.parent.acknowledgementText = """
        This file was originally developed by Sarah Frisken, Radiology, BWH and was partially funded
        by NIH grant R01EB027134-01.
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
        self.currentBlurinesssigma = 30
        self.currentBlurinessBorderValue = 40
        self.currentAudioThresholdValue = 40
        self.currentFlickerThresholdValue = 40


            
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

            self.sigma_slider.setMinimum(0.1)
            self.sigma_slider.setMaximum(1500)
            self.sigma_slider.valueChanged.connect(self.sigma_changed)
            
            self.threshold_slider.setMinimum(round(self.uncertaintyArray.min()*100))
            self.threshold_slider.setMaximum(round(self.uncertaintyArray.max()*100))
            self.threshold_slider.valueChanged.connect(self.bluriness_border_changed)
            self.threshold_slider.setValue(self.currentBlurinessBorderValue*10)

            self.audio_threshold_slider.setMinimum(round(self.uncertaintyArray.min()*100))
            self.audio_threshold_slider.setMaximum(round(self.uncertaintyArray.max()*100))
            self.audio_threshold_slider.valueChanged.connect(self.audio_threshold_changed)
            self.audio_threshold_slider.setValue(self.currentAudioThresholdValue*10)
            
            self.flicker_threshold_slider.setMinimum(round(self.uncertaintyArray.min()*100))
            self.flicker_threshold_slider.setMaximum(round(self.uncertaintyArray.max()*100))
            self.flicker_threshold_slider.valueChanged.connect(self.flicker_threshold_changed)
            self.flicker_threshold_slider.setValue(self.currentFlickerThresholdValue*10)

            
            self.cursorType.currentIndexChanged.connect(self.logic.onCursorchanged)
            self.changeBlurinessTofuzzinessOrBlackOut.currentIndexChanged.connect(self.onFilterChanged)


    def binaryColorMap(self, is_checked):
    
        if is_checked:
            self.logic.colorLUT.setisBinary(True)
        else:
            self.logic.colorLUT.setisBinary(False)

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
            self.x_slider_label.setText(str(value) + " mm")

    def change_opacity(self, Button, opacity):
    
            self.logic.tumorBasedViS.change_opacity(Button, opacity)
    
    def sigma_changed(self, sigma):
        
            self.currentBlurinesssigma = sigma
            self.logic.blurinessNumberOfSectionChanged(index =self.currentBlurinessIndex, blurinessIntencity=sigma/300, notBlureddUncertaintyIncrease =self.currentBlurinessBorderValue/100 )
    
    def bluriness_border_changed(self, bluriness_border):
            
            self.currentBlurinessBorderValue = bluriness_border
            self.logic.blurinessNumberOfSectionChanged( index =self.currentBlurinessIndex,blurinessIntencity= self.currentBlurinesssigma/300, notBlureddUncertaintyIncrease=bluriness_border/100)
            self.slider_value_label.setText(str(bluriness_border/100) + " mm")

    def audio_threshold_changed(self, new_threshold):
    
            self.currentAudioThresholdValue = new_threshold
            self.audio_slider_value_label.setText(str(new_threshold/100) + " mm")
            self.logic.audioMode.setThreshold(new_threshold)
            
    def flicker_threshold_changed(self, new_threshold):
    
            self.currentFlickerhresholdValue = new_threshold
            self.flicker_slider_value_label.setText(str(new_threshold/100) + " mm")
            self.logic.uncertaintyForeground.setFlickerThreshold(new_threshold)

    
    def bluriness_number_of_section_changed(self, index):
            
            self.currentBlurinessIndex = index
            self.logic.blurinessNumberOfSectionChanged(index = index, blurinessIntencity= self.currentBlurinesssigma/300, notBlureddUncertaintyIncrease =self.currentBlurinessBorderValue/100)
    
    def blurinessModeSelected(self, inChecked):
    
        if inChecked:
            
            self.logic.backgroundModifiedVisualization.visualizeBluredBackground()
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
        self.logic.blurinessNumberOfSectionChanged(index =self.currentBlurinessIndex, blurinessIntencity= self.currentBlurinesssigma/300, notBlureddUncertaintyIncrease =self.currentBlurinessBorderValue/100 )

    def resetColormapSelected(self):
        self.logic.colorLUT.resetLUTTogrey()
        self.x_slider.setValue(self.uncertaintyArray.min())
        
    
    def on_spinbox_value_changed(self, Button, value):
                
        self.logic.tumorBasedViS.set_line_width(Button, value)
    
    



    def setup(self):

        ScriptedLoadableModuleWidget.setup(self)
        

        directoryButton = qt.QPushButton("Select Image Volumes")
        self.layout.addWidget(directoryButton)
       # directoryButton.connect('clicked()', self.onDirectoryButtonClicked)
      #  directoryButton.styleSheet = "font-size: 16pt; color: orange; margin: 10px; background-color: rgb(10, 20, 33); border-width: 2px; border-style: outset; border-radius: 10px; border-style: inset"

        
        directoryButton = qt.QPushButton("Select Uncertainty Volume")
        self.layout.addWidget(directoryButton)
        directoryButton.connect('clicked()', self.onUncertaintyVolumeSelected)
       # directoryButton.styleSheet = "font-size: 16pt; color: orange; margin: 10px; background-color: rgb(10, 20, 33); border-width: 2px; border-style: outset; border-radius: 10px; border-style: inset"


        self.layout.addStretch(1)


        
        blurinessColapsibbleButton = ctk.ctkCollapsibleButton()
        blurinessColapsibbleButton.text = "Volume Filtering"
       # blurinessColapsibbleButton.styleSheet = "color: rgb(136, 152, 186);"

        self.layout.addWidget(blurinessColapsibbleButton)
        blurinessCollapsibleLayout = qt.QFormLayout(blurinessColapsibbleButton)

        blurinessLayout = qt.QGridLayout()
        
        
        
        blurinessLevelSliderLabel = qt.QLabel("Filter Level:")
        
        
        self.sigma_slider = qt.QSlider(qt.Qt.Horizontal)
        self.sigma_slider.setFocusPolicy(qt.Qt.StrongFocus)
        self.sigma_slider.setTickInterval(10)
        self.sigma_slider.setFixedSize(200, 30)
        self.sigma_slider.setValue(self.currentBlurinesssigma)


        blurinessLThresholdSlider = qt.QLabel("Uncertainty Threshold:")

    

        self.threshold_slider = qt.QSlider(qt.Qt.Horizontal)
        self.threshold_slider.setFocusPolicy(qt.Qt.StrongFocus)
        self.threshold_slider.setTickInterval(10)
        self.threshold_slider.setFixedSize(200, 30)
        self.threshold_slider.setValue(self.currentBlurinessBorderValue)
        
        self.slider_value_label = qt.QLabel(str(self.currentBlurinessBorderValue/10) + " mm")


        self.changeBlurinessTofuzzinessOrBlackOut = qt.QComboBox()
        self.changeBlurinessTofuzzinessOrBlackOut.setFixedSize(120, 30)
        self.changeBlurinessTofuzzinessOrBlackOut.addItem("Guassian")
        self.changeBlurinessTofuzzinessOrBlackOut.addItem("Noise")
        self.changeBlurinessTofuzzinessOrBlackOut.addItem("Transparancy")
        self.changeBlurinessTofuzzinessOrBlackOut.setCurrentIndex(0)

        
        self.numberofBluredSectionsDropdown = qt.QComboBox()
        self.numberofBluredSectionsDropdown.setFixedSize(50, 30)
        for value in range(2, 13):
            self.numberofBluredSectionsDropdown.addItem(str(value))
        self.numberofBluredSectionsDropdown.setCurrentIndex(0)
        self.numberofBluredSectionsDropdown.currentIndexChanged.connect(self.bluriness_number_of_section_changed)
        
        self.selectBlurinessCheckkBox = qt.QCheckBox("Enable")
        self.selectBlurinessCheckkBox.toggled.connect(lambda:self.blurinessModeSelected(self.selectBlurinessCheckkBox.isChecked()))
                

        
  
        blurinessLayout.addWidget(blurinessLevelSliderLabel, 1, 0)
        blurinessLayout.addWidget(self.changeBlurinessTofuzzinessOrBlackOut, 2, 2, qt.Qt.AlignRight)
        blurinessLayout.addWidget(self.numberofBluredSectionsDropdown, 3, 2, qt.Qt.AlignRight )
        blurinessLayout.addWidget(self.selectBlurinessCheckkBox, 0, 0, qt.Qt.AlignLeft)
        blurinessLayout.addWidget(self.sigma_slider, 2, 0)
        blurinessLayout.addWidget(blurinessLThresholdSlider, 3, 0)
        slider_layout = qt.QHBoxLayout()
        slider_layout.addWidget(self.threshold_slider)
        slider_layout.addWidget(self.slider_value_label)
        blurinessLayout.addLayout(slider_layout, 4, 0)
        blurinessCollapsibleLayout.addRow(blurinessLayout)


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
        self.binary_CheckBox.toggled.connect(lambda: self.binaryColorMap(self.binary_CheckBox.isChecked()))
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
        self.tumorBasedViS = TumorBasedViS(self.uncertaintyArray)
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
           self.backgroundModifiedVisualization.visualizeBluredBackground(sigmas,uncertaintyBorders, currentNumberofSections)


        
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

            

    
class UncertaintyForegroundVisualization():

    def __init__(self, uncertaintyNode):
    
        self.surgeonCentricMargin = 10
        self.mask = self.shpere_mask(self.surgeonCentricMargin)
        # Node to display uncertainty in this layer
        self.uncertaintyVISVolumeNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode", 'Uncertainty_Foreground')
        v1 = slicer.util.getNode('ref_ref_t2')
        self.origin = v1.GetOrigin()
        self.uncertaintyVISVolumeNode.SetOrigin(self.origin)
        # Node for the main uncertainty
        self.uncertaintyNode = None
        # array for the main uncertainty
        self.uncertaintyArray = None
        self.isSurgeonCentric = False
        self.lookupTable = None
        self.opacity = None
        self.FLICKER_INTERVAL_MS = 400
        self.flickerTimer = qt.QTimer()
        self.flickerTimer.setInterval(self.FLICKER_INTERVAL_MS)
        self.flickerTimer.timeout.connect(self.toggleFlicker)
        self.current_visibility = False
        self.initializeNodes(uncertaintyNode)
        self.updateForegroundWithArray(self.uncertaintyArray)
        self.initiateUncertaintyVISVolumeNode()
        self.displayNode =  self.uncertaintyVISVolumeNode.GetDisplayNode()
        self.flickerIsOn = False
        self.flickerThreshold = 4
        self.alreadyInFlicker = False

    def setFlickerThreshold(self, threshold):
                    self.flickerThreshold = threshold/100

    def initiateUncertaintyVISVolumeNode(self):
    
      #  self.uncertaintyVISVolumeNode.SetDisplayVisibility(True)
        imageDirections = [[1,0,0], [0,1,0], [0,0,1]]
        imageSpacing = [0.5, 0.5, 0.5]
        self.uncertaintyVISVolumeNode.SetIJKToRASDirections(imageDirections)
        self.uncertaintyVISVolumeNode.SetSpacing(imageSpacing)
        slicer.util.setSliceViewerLayers(foreground=self.uncertaintyVISVolumeNode, foregroundOpacity=0.0)
    
    def initializeNodes(self, uncertaintyNode):
        
        self.uncertaintyNode = uncertaintyNode
        self.uncertaintyArray = slicer.util.arrayFromVolume(self.uncertaintyNode)

    def setSurgeonCentricMode(self, surgeonCentricMode):
                    
        self.isSurgeonCentric = surgeonCentricMode
            
         
    def turnOff(self, isChecked):
        
        if not isChecked:
            
            slicer.util.setSliceViewerLayers(foreground=self.uncertaintyVISVolumeNode, foregroundOpacity=0.0)
        
        else:
            
            slicer.util.setSliceViewerLayers(foreground=self.uncertaintyVISVolumeNode, foregroundOpacity=0.5)

            
    
    def updateForegroundWithArray(self, update_array):
        
        if self.isSurgeonCentric:
            update_array[~self.mask] = 0
        
        slicer.util.updateVolumeFromArray(self.uncertaintyVISVolumeNode, update_array)
        
                
    def shpere_mask(self, radius):

        center = (int(radius), int(radius), int(radius))

        gh = radius*2

        Y, X, Z = np.ogrid[:gh, :gh, :gh]

        dist_from_center = np.sqrt((X - center[0])**2 + (Y-center[1])**2 + (Z-center[1])**2)

        mask = dist_from_center <= radius

        return mask
            
            
        
    def visualize(self, ras =  [1.0, 1.0, 1.0] ,point_Ijk = [0, 0, 0]):
    
        if self.isSurgeonCentric:
            try:
                
                slicer.util.setSliceViewerLayers(foreground=self.uncertaintyVISVolumeNode, foregroundOpacity=0.5)
                uncertaintyArray_croped = self.surgeonCentricArrayCalculation(point_Ijk)
                self.updateForegroundWithArray(uncertaintyArray_croped)
                self.uncertaintyVISVolumeNode.SetOrigin([ras[0]-(self.surgeonCentricMargin/2), ras[1]-(self.surgeonCentricMargin/2), ras[2]-(self.surgeonCentricMargin/2)])
                
            except Exception as e:
                pass
        else:
                
              #  slicer.util.setSliceViewerLayers(foreground=self.uncertaintyVISVolumeNode, foregroundOpacity=0.0)

                self.updateForegroundWithArray(self.uncertaintyArray)
                self.uncertaintyVISVolumeNode.SetOrigin(self.origin)
                
    def toggleFlicker(self):
    
            
            if not self.current_visibility:
                slicer.util.setSliceViewerLayers(foreground=self.uncertaintyVISVolumeNode, foregroundOpacity=0.4)
                self.current_visibility = True
            else:
                slicer.util.setSliceViewerLayers(foreground=self.uncertaintyVISVolumeNode, foregroundOpacity=0.0)
                self.current_visibility = False

    def startFlicker(self):
        self.flickerTimer.start()

    def stopFlicker(self):
        self.flickerTimer.stop()
       # slicer.util.setSliceViewerLayers(foreground=self.uncertaintyVISVolumeNode, foregroundOpacity=0.5)
        self.current_visibility = False

    #    self.uncertaintyVISVolumeNode.SetOrigin([ras[0]-(self.surgeonCentricMargin/2), ras[1]-(self.surgeonCentricMargin/2), ras[2]-(self.surgeonCentricMargin/2)])

        
        

    def performFlicker(self, point_Ijk):
            
            try:
                if self.flickerIsOn:
                    if self.uncertaintyArray[point_Ijk[2]][point_Ijk[1]][point_Ijk[0]] > self.flickerThreshold:
                        if not self.alreadyInFlicker:
                            self.alreadyInFlicker = True
                            self.startFlicker()
                
                    else:
                        self.stopFlicker()
                        self.alreadyInFlicker = False
                        
            except Exception as e:
                pass
                
                
                
    def showFlicker(self, isChecked):
            
            self.flickerIsOn = isChecked
            if not isChecked:
                self.stopFlicker()


    def surgeonCentricArrayCalculation(self, point_Ijk):
        
        lefti = point_Ijk[0]- self.surgeonCentricMargin
        righti = point_Ijk[0] + self.surgeonCentricMargin

        leftj = point_Ijk[1] - self.surgeonCentricMargin
        rigthj = point_Ijk[1] + self.surgeonCentricMargin

        leftk = point_Ijk[2] - self.surgeonCentricMargin
        rightk = point_Ijk[2] + self.surgeonCentricMargin


        if lefti < 0:
            lefti = 0

        if leftj < 0:
            leftj = 0

        if leftk < 0:
            leftk = 0
            
        uncertaintyArray_copy = self.uncertaintyArray.copy()
        uncertaintyArray_croped = uncertaintyArray_copy[leftk:rightk, leftj:rigthj, lefti:righti]
        
        uncertaintyArray_croped = uncertaintyArray_croped - self.uncertaintyArray.min()
        uncertaintyArray_croped = uncertaintyArray_croped /(self.uncertaintyArray.max() - self.uncertaintyArray.min())

        uncertaintyArray_croped = uncertaintyArray_croped *255

        return uncertaintyArray_croped


    def apply_threshold(self, threshold):
        
            self.displayNode.SetApplyThreshold(1)
            self.displayNode.SetLowerThreshold(threshold)

class BackgroundModifiedVisualization():

    def __init__(self, uncertaintyArray):
        
        self.BackgroundModifedVisualization = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode","BackgroundModifedVisualization")
        imageDirections = [[1,0,0], [0,1,0], [0,0,1]]
        imageSpacing = [0.5, 0.5, 0.5]
        self.BackgroundModifedVisualization.SetIJKToRASDirections(imageDirections)
        self.BackgroundModifedVisualization.SetSpacing(imageSpacing)
        
        self.backgroundToBemodified = slicer.util.array('ref_ref_t2')
        self.mainBackground = slicer.util.getNode('ref_ref_t2')
        self.origin = self.mainBackground.GetOrigin()
        self.BackgroundModifedVisualization.SetOrigin(self.origin)
        self.filterType = "Blur"

        self.uncertaintyArray = uncertaintyArray
        
        self.initializeBluringVariables()

    def initializeBluringVariables(self):
        
        self.numberOfSections = 2
        self.sigmas = [0, 3]
        self.bluredArrays = []
        self.masks = []
        self.uncertaintyBorders = [self.uncertaintyArray.min(), 4 ,self.uncertaintyArray.max()]
        self.masked_uncertainty_volumes = []
        self.blured_masked_volumes = []

    
    def setBlurringVariables(self, sigmas, uncertaintyBorders ):
        
        self.sigmas = sigmas
        self.uncertaintyBorders = uncertaintyBorders
        
    def setFilterType(self, filterType):
        self.filterType = filterType
        
    def resetBlurringVariables(self):
        
        self.bluredArrays = []
        self.masks = []
        self.masked_uncertainty_volumes = []
        self.blured_masked_volumes = []
        
    def add_gaussian_noise(self, volume, mean=0, std=1):
        noise = np.random.normal(mean, std, size=volume.shape)
        return volume + noise
        
    def adjust_brightness(self, volume, factor):

            if factor == 0:
                        adjusted_volume = volume
            else:
                    adjusted_volume = np.clip(volume * factor, 0, 255).astype(np.uint8)

            return adjusted_volume
        
    def visualizeBluredBackground(self, sigmas = None, uncertaintyBorders =None, numberOfSections = None):
        

        if numberOfSections is not None:
            self.numberOfSections = numberOfSections
            
        if sigmas is not None and uncertaintyBorders is not None:
            self.setBlurringVariables(sigmas, uncertaintyBorders)
        
        for sigma in self.sigmas:

            if self.filterType == "Blur":
                self.bluredArrays.append(gaussian_filter(self.backgroundToBemodified, sigma=sigma))
            elif self.filterType == "Noise":
                self.bluredArrays.append(self.add_gaussian_noise(self.backgroundToBemodified,mean=0, std=sigma*7))
            elif self.filterType == "Light":
                self.bluredArrays.append(self.adjust_brightness(self.backgroundToBemodified, sigma/40))

        for i in range(self.numberOfSections):

            self.masks.append(np.logical_and(self.uncertaintyArray >= self.uncertaintyBorders[i], self.uncertaintyArray <= self.uncertaintyBorders[i+1]))



        uncertaintyArrayCopy = self.uncertaintyArray.copy()

        for mask in self.masks:
        
            self.masked_uncertainty_volumes.append(uncertaintyArrayCopy * mask)

        for i in range(self.numberOfSections):

            self.blured_masked_volumes.append(self.bluredArrays[i] * self.masks[i])

        self.bluredFinalVolumeArray  = self.blured_masked_volumes[0]

        for i, blured_masked_volume in enumerate(self.blured_masked_volumes):
        
            if i != 0 :
                self.bluredFinalVolumeArray += blured_masked_volume

        slicer.util.updateVolumeFromArray(self.BackgroundModifedVisualization, self.bluredFinalVolumeArray)


        self.resetBlurringVariables()
        slicer.util.setSliceViewerLayers(background=self.BackgroundModifedVisualization)
        

    def turnBluredVisualizationOff(self):
    
        slicer.util.setSliceViewerLayers(background=self.mainBackground)



class TexModeVisualization():


    def __init__(self, uncertaintyArray):
    
    
        self.markupsNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
        self.markupsNode.AddControlPoint([0,0,0])
        self.markupsNode.SetDisplayVisibility(False)
        self.markupsNode.GetDisplayNode().SetUseGlyphScale(0)
        self.markupsNode.GetDisplayNode().SetGlyphType(3)
        self.markupsNode.GetDisplayNode().SetSelectedColor(0,1,0)
        self.markupsNode.GetDisplayNode().SetActiveColor(0,1,0)
        self.markupsNode.GetDisplayNode().SetTextScale(4)
        self.uncertaintyArray = uncertaintyArray
        
        self.isOn = False

        
    def showMarkup(self, isChecked):
     
            self.markupsNode.SetDisplayVisibility(isChecked)
            self.isOn = isChecked

    def changeGlyphType(self, index):
                
                self.markupsNode.GetDisplayNode().SetGlyphType(index)
                if index == 6:
                    self.markupsNode.GetDisplayNode().SetOpacity(0.3)

                else:
                    self.markupsNode.GetDisplayNode().SetOpacity(1)
            
    def moveMarkup(self, ras, point_Ijk):
            
            if self.isOn:
                try:
                
                    self.markupsNode.SetNthControlPointLabel(0,  u"\u00B1 " +  str(round(self.uncertaintyArray[point_Ijk[2]][point_Ijk[1]][point_Ijk[0]], 2)) + " mm" )
                    self.markupsNode.SetNthControlPointPosition(0, ras[0], ras[1], ras[2])
                    self.markupsNode.GetDisplayNode().SetGlyphSize(round(self.uncertaintyArray[point_Ijk[2]][point_Ijk[1]][point_Ijk[0]], 2))
                
                except Exception as e:
                    pass
                    
        
     #   self.markupsNode.GetDisplayNode().SetViewNodeIDs(["vtkMRMLSliceNodeRed"])
   

class AudioMode():
    
    def __init__(self, uncertaintyArray):
        
            self.uncertaintyArray = uncertaintyArray
            #todo: change this
            self.audioPath = "Users/mahsa/BWH/Data/"
            self.audioFileList = ["beep1.mp3", "beep2.mp3", "dontTrust.mp3"]
            self.audioFileName = "beep1.mp3"
        
            self.previousPosition = [-100, -100, -100]
            # Todo: check this
            self.inSafeArea = True
            self.detectedUncertaintyHigherthanThresholdPosition = None
            self.threshold = 5
            self.isOn = False
       
    
            
    def setAudioFile(self, index):
            self.audioFileName = self.audioFileList[index]

            
    def turnOnAudioMode(self, isChecked):
                        
            self.isOn = isChecked

    def setThreshold(self, threshold):
        
        self.threshold = threshold/100
            
    def performAudioMode(self, point_Ijk):
            
            try:
                if self.isOn:
                    if self.uncertaintyArray[point_Ijk[2]][point_Ijk[1]][point_Ijk[0]] > self.threshold:
                        if self.inSafeArea:
                            self.inSafeArea = False
                            
                            #todo: why 0.1?
                            distance = math.sqrt((self.previousPosition[0] - point_Ijk[0])**2 + (self.previousPosition[1] - point_Ijk[1])**2 + (self.previousPosition[2] - point_Ijk[2])**2)

                            if distance > 0.1:
                                playsound(self.audioPath + self.audioFileName)
                            
                            self.previousPosition = point_Ijk
                    
                    else:
                        if self.inSafeArea is not True:
                            self.inSafeArea = True
            except Exception as e:
                pass


    
class ColorLUT():

    def __init__(self, uncertaintyVISVolumeNode):
        
        self.firstColor = None
        self.secondColor = None
        self.threshold = 122
        self.uncertaintyVISVolumeNode = uncertaintyVISVolumeNode
        self.displayNode = self.uncertaintyVISVolumeNode.GetDisplayNode()
        self.isBinary = False
        self.colorTable = None
        self.colorTableForSurgeonCentric = None
        self.oneColor = False
        self.isSurgeonCentric = False
    
    def resetColors(self):
        
        self.firstColor = None
        self.secondColor = None
    
    def resetLUTTogrey(self):
        
        self.resetColors()
        self.displayNode.SetAndObserveColorNodeID("vtkMRMLColorTableNodeGrey")
        self.displayNode.SetApplyThreshold(0)


        
    def setSecondColor(self, secondColor):
    
        self.secondColor = secondColor
        self.secondColor = tuple(component / 255 for component in self.secondColor)

    
    def setFirstColor(self, firstColor):
    
        self.firstColor = firstColor
        self.firstColor = tuple(component / 255 for component in self.firstColor)

    def setisBinary(self, isBinary):
        self.isBinary = isBinary

    
    def applyColorMap(self):
        
        if self.firstColor is  not None:
            slicer.mrmlScene.RemoveNode(self.colorTable)
            slicer.mrmlScene.RemoveNode(self.colorTableForSurgeonCentric)
            
            self.colorTable = slicer.vtkMRMLColorTableNode()
            self.colorTable.SetTypeToUser()
            self.colorTable.SetNumberOfColors(256)
            self.colorTable.SetName("Test")
            
            self.colorTableForSurgeonCentric = slicer.vtkMRMLColorTableNode()
            self.colorTableForSurgeonCentric.SetTypeToUser()
            self.colorTableForSurgeonCentric.SetNumberOfColors(256)
            self.colorTableForSurgeonCentric.SetName("Test")
                
            if self.secondColor is None:
                self.secondColor = [1.0, 1.0, 1.0]

            if self.isBinary:
                self.applyBinary()
            
            else:
                self.applyGradient()
            
                        
            
    def applyGradient(self):

            gradient = np.linspace(0, 1, 256)
            gradient_array = np.outer(gradient, self.firstColor) + np.outer((1 - gradient), self.secondColor)
            
            for i in range(0,255):
                if i == 0:
                    self.colorTableForSurgeonCentric.SetColor(i, gradient_array[i][0],gradient_array[i][1],gradient_array[i][2], 0.0)
                else:
                    self.colorTableForSurgeonCentric.SetColor(i, gradient_array[i][0],gradient_array[i][1],gradient_array[i][2], 1.0)

                self.colorTable.SetColor(i, gradient_array[i][0],gradient_array[i][1],
                gradient_array[i][2], 1.0)
        
            slicer.mrmlScene.AddNode(self.colorTable)
            slicer.mrmlScene.AddNode(self.colorTableForSurgeonCentric)
            
            if self.isSurgeonCentric:
                self.displayNode.SetAndObserveColorNodeID(self.colorTableForSurgeonCentric.GetID())
            else:
                self.displayNode.SetAndObserveColorNodeID(self.colorTable.GetID())

           # self.displayNode.SetThreshold(6, 10)


    def applyBinary(self):
        
            for i in range(0,255):

                if i > self.threshold:
                    self.colorTable.SetColor(i, self.firstColor[0], self.firstColor[1], self.firstColor[2], 1.0)
                    self.colorTableForSurgeonCentric.SetColor(i, self.firstColor[0], self.firstColor[1], self.firstColor[2], 1.0)
                else:
                    if self.oneColor:
                        self.colorTable.SetColor(i, self.secondColor[0], self.secondColor[1], self.secondColor[2], 0.0)
                        self.colorTableForSurgeonCentric.SetColor(i, self.secondColor[0], self.secondColor[1], self.secondColor[2], 0.0)
                    else:
                        if i == 0:
                            self.colorTableForSurgeonCentric.SetColor(i, self.secondColor[0], self.secondColor[1], self.secondColor[2], 0.0)
                        else:
                            self.colorTableForSurgeonCentric.SetColor(i, self.secondColor[0], self.secondColor[1], self.secondColor[2], 1.0)
                        self.colorTable.SetColor(i, self.secondColor[0], self.secondColor[1], self.secondColor[2], 1.0)


            slicer.mrmlScene.AddNode(self.colorTable)
            slicer.mrmlScene.AddNode(self.colorTableForSurgeonCentric)
            
            
            if self.isSurgeonCentric:
                self.displayNode.SetAndObserveColorNodeID(self.colorTableForSurgeonCentric.GetID())
            else:
                self.displayNode.SetAndObserveColorNodeID(self.colorTable.GetID())

          #  self.displayNode.SetThreshold(6, 10)
            
            

class TumorBasedViS():

    def __init__(self, uncertainty_array):
        
        self.smaller_model = None
        self.larger_model = None
        self.surface_model = None
        
        self.modelPolyData = None
        
        self.smaller_mode_display_node = None
        self.larger_model_display_node = None
        self.surface_mode_display_node = None
        
        self.volumeRasToIjk = None
        self.surface_model_threshold = 0.5
        self.surface_model_smoth = 30
        self.surface_model_decimate = 0.5
        self.uncertainty_array = uncertainty_array
        
        self.points = None
        self.point_data = None
        self.normals = None
        
        self.temporary_init()
        self.calculate_uncertatinty_volumes()
      
    
        

    # todo: change it
    def temporary_init(self):
    
        self.larger_model = slicer.util.getNode('Output4')
        self.larger_mode_display_node = self.larger_model.GetDisplayNode()
        self.modelOutputPoly = self.larger_model.GetPolyData()

        self.smaller_model = slicer.util.getNode('Output5')
        self.smaller_mode_display_node = self.smaller_model.GetDisplayNode()
        self.modelOutputPoly_small = self.smaller_model.GetPolyData()
        
        self.surface_model = slicer.util.getNode('Output3')
        self.surface_mode_display_node = self.surface_model.GetDisplayNode()

        self.modelPolyData = self.surface_model.GetPolyData()
        
        volumeNode = slicer.util.getNode('Segmentation-Tumor-label_1')
        self.volumeRasToIjk = vtk.vtkMatrix4x4()
        volumeNode.GetRASToIJKMatrix(self.volumeRasToIjk)
        
        self.points = self.modelPolyData.GetPoints()
        self.point_data = self.modelPolyData.GetPointData()
        self.normals = self.point_data.GetNormals()

        self.model_bigger_points = self.modelOutputPoly.GetPoints()
        self.model_smaller_points = self.modelOutputPoly_small.GetPoints()


    def enable_tumorVIS(self, is_checked):
        
        if is_checked:
        
            self.larger_mode_display_node.VisibilityOn()
            self.surface_mode_display_node.VisibilityOn()
            self.smaller_mode_display_node.VisibilityOn()
        
        else:
            
            self.larger_mode_display_node.VisibilityOff()
            self.surface_mode_display_node.VisibilityOff()
            self.smaller_mode_display_node.VisibilityOff()
        
            


    def calculate_uncertatinty_volumes(self):
        
        for i in range(self.points.GetNumberOfPoints()):

            point = [0.0, 0.0, 0.0]
            self.points.GetPoint(i, point)
            
        # Get ijk of ith point
            point_Ijk = [0, 0, 0, 1]
            self.volumeRasToIjk.MultiplyPoint(np.append(point,1.0), point_Ijk)
            point_Ijk = [ int(round(c)) for c in point_Ijk[0:3] ]

            uncertainty_value = self.uncertainty_array[point_Ijk[2]][point_Ijk[1]][point_Ijk[0]]/2

            # Get normal of ith point
            normal = [0.0, 0.0, 0.0]
            self.normals.GetTuple(i, normal)

            # Get unit_vect
            unit_vec = self.getUnitVec(normal)

            # new point for bigger volume
            new_distance = [uncertainty_value * v for v in unit_vec]
            new_point_bigger = [p + d for p,d in zip(point, new_distance)]
            self.model_bigger_points.SetPoint(i, new_point_bigger )

            # new point for smaller volume
            flipped_unit_vec = [-v for v in unit_vec]
            
            new_distance_smaller = [uncertainty_value * v for v in flipped_unit_vec]
            new_point_smaller = [p2 + d2 for p2,d2 in zip(point, new_distance_smaller)]
            self.model_smaller_points.SetPoint(i, new_point_smaller )

            self.modelOutputPoly.GetPoints().Modified()
            self.modelOutputPoly_small.GetPoints().Modified()
            slicer.app.processEvents()
    
    
    def change_opacity(self, Button, opacity):
    
        if Button == Button.TumorBigger:
            
            self.larger_mode_display_node.SetOpacity(opacity/100)
            self.larger_mode_display_node.SetSliceIntersectionOpacity(opacity/100)

        elif Button == Button.Tumor:
            
            self.surface_mode_display_node.SetOpacity(opacity/100)
            self.surface_mode_display_node.SetSliceIntersectionOpacity(opacity/100)
            
        elif Button == Button.TumorSmaller:
        
            self.smaller_mode_display_node.SetOpacity(opacity/100)
            self.smaller_mode_display_node.SetSliceIntersectionOpacity(opacity/100)

        
    def set_color(self, Button, color):
    
        color = tuple(c/255 for c in color)
        
        if Button == Button.TumorBigger:
            
            self.larger_mode_display_node.SetColor(color)

        elif Button == Button.Tumor:
            
            self.surface_mode_display_node.SetColor(color)
            
        elif Button == Button.TumorSmaller:
        
            self.smaller_mode_display_node.SetColor(color)

        
    def set_line_width(self, Button, width):

        if Button == Button.TumorBigger:
            
            self.larger_mode_display_node.SetSliceIntersectionThickness(width)

        elif Button == Button.Tumor:
            
            print("HIIII")
            self.surface_mode_display_node.SetSliceIntersectionThickness(width)
            
        elif Button == Button.TumorSmaller:
        
            self.smaller_mode_display_node.SetSliceIntersectionThickness(width)

        
        
        
    
    def getUnitVec(self, normal):

        normal_magnitude = math.sqrt(sum(n**2 for n in normal))
        
        return [n / normal_magnitude for n in normal]
        
        
    
        
        
        
        
        
    
    
        
    
    