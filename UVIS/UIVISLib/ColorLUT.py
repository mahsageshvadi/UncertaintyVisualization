import numpy as np
import slicer
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

    def reset_colors(self):

        self.firstColor = None
        self.secondColor = None

    def reset_lut_togrey(self):

        self.reset_colors()
        self.displayNode.SetAndObserveColorNodeID("vtkMRMLColorTableNodeGrey")
        self.displayNode.SetApplyThreshold(0)

    def set_second_color(self, secondColor):

        self.secondColor = secondColor
        self.secondColor = tuple(component / 255 for component in self.secondColor)

    def set_first_color(self, firstColor):

        self.firstColor = firstColor
        self.firstColor = tuple(component / 255 for component in self.firstColor)

    def set_is_binary(self, isBinary):
        self.isBinary = isBinary

    def apply_color_map(self):

        if self.firstColor is not None:
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
                self.apply_binary()

            else:
                self.apply_gradient()

    def apply_gradient(self):

        gradient = np.linspace(0, 1, 256)
        gradient_array = np.outer(gradient, self.firstColor) + np.outer((1 - gradient), self.secondColor)

        for i in range(0, 255):
            if i == 0:
                self.colorTableForSurgeonCentric.SetColor(i, gradient_array[i][0], gradient_array[i][1],
                                                          gradient_array[i][2], 0.0)
            else:
                self.colorTableForSurgeonCentric.SetColor(i, gradient_array[i][0], gradient_array[i][1],
                                                          gradient_array[i][2], 1.0)

            self.colorTable.SetColor(i, gradient_array[i][0], gradient_array[i][1],
                                     gradient_array[i][2], 1.0)

        slicer.mrmlScene.AddNode(self.colorTable)
        slicer.mrmlScene.AddNode(self.colorTableForSurgeonCentric)

        if self.isSurgeonCentric:
            self.displayNode.SetAndObserveColorNodeID(self.colorTableForSurgeonCentric.GetID())
        else:
            self.displayNode.SetAndObserveColorNodeID(self.colorTable.GetID())

    # self.displayNode.SetThreshold(6, 10)

    def apply_binary(self):

        for i in range(0, 255):

            if i > self.threshold:
                self.colorTable.SetColor(i, self.firstColor[0], self.firstColor[1], self.firstColor[2], 1.0)
                self.colorTableForSurgeonCentric.SetColor(i, self.firstColor[0], self.firstColor[1], self.firstColor[2],
                                                          1.0)
            else:
                if self.oneColor:
                    self.colorTable.SetColor(i, self.secondColor[0], self.secondColor[1], self.secondColor[2], 0.0)
                    self.colorTableForSurgeonCentric.SetColor(i, self.secondColor[0], self.secondColor[1],
                                                              self.secondColor[2], 0.0)
                else:
                    if i == 0:
                        self.colorTableForSurgeonCentric.SetColor(i, self.secondColor[0], self.secondColor[1],
                                                                  self.secondColor[2], 0.0)
                    else:
                        self.colorTableForSurgeonCentric.SetColor(i, self.secondColor[0], self.secondColor[1],
                                                                  self.secondColor[2], 1.0)
                    self.colorTable.SetColor(i, self.secondColor[0], self.secondColor[1], self.secondColor[2], 1.0)

        slicer.mrmlScene.AddNode(self.colorTable)
        slicer.mrmlScene.AddNode(self.colorTableForSurgeonCentric)

        if self.isSurgeonCentric:
            self.displayNode.SetAndObserveColorNodeID(self.colorTableForSurgeonCentric.GetID())
        else:
            self.displayNode.SetAndObserveColorNodeID(self.colorTable.GetID())

    #  self.displayNode.SetThreshold(6, 10)