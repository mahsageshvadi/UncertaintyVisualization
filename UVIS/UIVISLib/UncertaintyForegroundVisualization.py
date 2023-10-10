import numpy as np
import slicer

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

                uncertaintyArray_croped = self.surgeonCentricArrayCalculation(point_Ijk)
                self.updateForegroundWithArray(uncertaintyArray_croped)
                slicer.util.setSliceViewerLayers(foreground=self.uncertaintyVISVolumeNode, foregroundOpacity=0.5)

                self.uncertaintyVISVolumeNode.SetOrigin([ras[0]-(self.surgeonCentricMargin/2), ras[1]-(self.surgeonCentricMargin/2), ras[2]-(self.surgeonCentricMargin/2)])

            except Exception as e:
                pass
        else:

                slicer.util.setSliceViewerLayers(foreground=self.uncertaintyVISVolumeNode, foregroundOpacity=0.0)

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

# Different filters