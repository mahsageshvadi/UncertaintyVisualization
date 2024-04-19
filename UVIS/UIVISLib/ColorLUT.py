import numpy as np
import slicer
import matplotlib
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
        self.uncertaintyArray = slicer.util.arrayFromVolume(uncertaintyVISVolumeNode)

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

       # number_of_uncertainty_ranges = round(self.uncertaintyArray.max())

        gradient = np.linspace(0, 1, 256)
        gradient_array = np.outer(gradient, self.firstColor) + np.outer((1 - gradient), self.secondColor)

        r = np.linspace(self.firstColor[0], self.secondColor[0], 256)
        g = np.linspace(self.firstColor[1], self.secondColor[1], 256)
        b = np.linspace(self.firstColor[2], self.secondColor[2], 256)

        gradient_colors = np.stack((r, g, b), axis=1)
        #slot_size = 255/number_of_uncertainty_ranges

       # for number_of_ranges in range(number_of_uncertainty_ranges):
            #for i in range(slot_size * number_of_ranges , slot_size * (number_of_ranges + 1))

     #   for i in range(0, 255):

              #  if i == 0:
             #       self.colorTableForSurgeonCentric.SetColor(i, gradient_colors[i][0], gradient_colors[i][1],
                                                #             gradient_colors[i][2], 0.0)
             #   else:
               #     self.colorTableForSurgeonCentric.SetColor(i, gradient_colors[i][0], gradient_colors[i][1],
                                                    #          gradient_colors[i][2], 1.0)

               # self.colorTable.SetColor(i, gradient_colors[i][0], gradient_colors[i][1],
                                         #gradient_colors[i][2], 1.0)

        colormap = matplotlib.colors.LinearSegmentedColormap.from_list("custom_gradient",
                                                                   [self.firstColor, self.secondColor])

        n_colors = 5
        colors = colormap(np.linspace(0, 1, n_colors))

        for i in range(0, 50):

            if i == 0:
                    self.colorTable.SetColor(i, 0,0,0, 0.0)
                    self.colorTableForSurgeonCentric.SetColor(i, 0,0,0, 0.0)
            else:
                    self.colorTable.SetColor(i, colors[0][0], colors[0][1], colors[0][2], 1.0)
                    self.colorTableForSurgeonCentric.SetColor(i, colors[0][0], colors[0][1], colors[0][2], 1.0)

        for i in range(50, 100):

            self.colorTable.SetColor(i, colors[1][0], colors[1][1], colors[1][2], 1.0)
            self.colorTableForSurgeonCentric.SetColor(i, colors[1][0], colors[1][1], colors[1][2], 1.0)

        for i in range(100, 150):

            self.colorTable.SetColor(i, colors[2][0], colors[2][1], colors[2][2], 1.0)
            self.colorTableForSurgeonCentric.SetColor(i, colors[2][0], colors[2][1], colors[2][2], 1.0)

        for i in range(150, 200):

            self.colorTable.SetColor(i, colors[3][0], colors[3][1], colors[3][2], 1.0)
            self.colorTableForSurgeonCentric.SetColor(i, colors[3][0], colors[3][1], colors[3][2], 1.0)

        for i in range(200, 255):
            self.colorTable.SetColor(i, colors[4][0], colors[4][1], colors[4][2], 1.0)
            self.colorTableForSurgeonCentric.SetColor(i, colors[4][0], colors[4][1], colors[4][2], 1.0)

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

    def game_level_changes(self, uncertaintyVISVolumeNode):
        self.uncertaintyVISVolumeNode = uncertaintyVISVolumeNode
        self.uncertaintyArray = slicer.util.arrayFromVolume(uncertaintyVISVolumeNode)
        self.apply_color_map()

    #  self.displayNode.SetThreshold(6, 10)