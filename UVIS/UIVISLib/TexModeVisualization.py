import slicer
class TexModeVisualization():

    def __init__(self, uncertaintyArray):

        self.markupsNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
        self.markupsNode.AddControlPoint([0, 0, 0])
        self.markupsNode.SetDisplayVisibility(False)
        self.markupsNode.GetDisplayNode().SetUseGlyphScale(0)
        self.markupsNode.GetDisplayNode().SetGlyphType(3)
        self.markupsNode.GetDisplayNode().SetSelectedColor(0, 1, 0)
        self.markupsNode.GetDisplayNode().SetActiveColor(0, 1, 0)
        self.markupsNode.GetDisplayNode().SetTextScale(4)
        self.uncertaintyArray = uncertaintyArray

        self.isOn = False

    def show_markup(self, isChecked):

        self.markupsNode.SetDisplayVisibility(isChecked)
        self.isOn = isChecked

    def change_glyph_type(self, index):


        self.markupsNode.GetDisplayNode().SetGlyphType(index)
        if index == 6:
            self.markupsNode.GetDisplayNode().SetOpacity(0.3)

        else:
            self.markupsNode.GetDisplayNode().SetOpacity(1)

    def move_markup(self, ras, point_Ijk):
        if self.isOn:
            try:

                self.markupsNode.SetNthControlPointLabel(0, u"\u00B1 " + str(
                    round(self.uncertaintyArray[point_Ijk[2]][point_Ijk[1]][point_Ijk[0]])) + " mm")
                self.markupsNode.SetNthControlPointPosition(0, ras[0], ras[1], ras[2])
                self.markupsNode.GetDisplayNode().SetGlyphSize(
                    round(self.uncertaintyArray[point_Ijk[2]][point_Ijk[1]][point_Ijk[0]], 2))

            except Exception as e:
                pass

    #   self.markupsNode.GetDisplayNode().SetViewNodeIDs(["vtkMRMLSliceNodeRed"])

