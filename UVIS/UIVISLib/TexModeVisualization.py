import slicer
import vtk
import numpy as np
class TexModeVisualization():

    def __init__(self, uncertaintyArray, uncertaintyNode):

        self.markupsNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
        self.markupsNode.AddControlPoint([0, 0, 0])
        self.markupsNode.SetDisplayVisibility(False)
        self.markupsNode.GetDisplayNode().SetUseGlyphScale(0)
        self.markupsNode.GetDisplayNode().SetGlyphType(3)
        self.markupsNode.GetDisplayNode().SetSelectedColor(0, 1, 0)
        self.markupsNode.GetDisplayNode().SetActiveColor(0, 1, 0)
        self.markupsNode.GetDisplayNode().SetTextScale(4)
        self.uncertaintyArray = uncertaintyArray
        self.change_cursor_positions = [[41.242528337525826, 114.516499066434, 19.518448539923476],
                                        [-41.750913488073635, -14.288212675131298, 11.580703735351562],
                                        [12.137938256273756, 32.12857736058601, 69.16075134277342],
                                        [24.95667196547288, 269.6298491832088, -108.05052185058592]]
        self.uncertaintyNode = uncertaintyNode
        self.current_level = 0
        self.isOn = False

    def show_markup(self, isChecked):

        self.markupsNode.SetDisplayVisibility(isChecked)
        self.isOn = isChecked
        ras = self.change_cursor_positions[self.current_level]
        volumeRasToIjk = vtk.vtkMatrix4x4()
        self.uncertaintyNode.GetRASToIJKMatrix(volumeRasToIjk)

        point_Ijk = [0, 0, 0, 1]
        volumeRasToIjk.MultiplyPoint(np.append(ras, 1.0), point_Ijk)
        point_Ijk = [int(round(c)) for c in point_Ijk[0:3]]
        self.move_markup(ras, point_Ijk)


    def change_glyph_type(self, index):

        self.markupsNode.GetDisplayNode().SetGlyphType(index)
        if index == 6:
            self.markupsNode.GetDisplayNode().SetOpacity(0.3)

        else:
            self.markupsNode.GetDisplayNode().SetOpacity(1)
        ras = self.change_cursor_positions[self.current_level]
        volumeRasToIjk = vtk.vtkMatrix4x4()
        self.uncertaintyNode.GetRASToIJKMatrix(volumeRasToIjk)

        point_Ijk = [0, 0, 0, 1]
        volumeRasToIjk.MultiplyPoint(np.append(ras, 1.0), point_Ijk)
        point_Ijk = [int(round(c)) for c in point_Ijk[0:3]]
        self.move_markup(ras, point_Ijk)

    def move_markup(self, ras, point_Ijk):
        if self.isOn:
            try:

                self.markupsNode.SetNthControlPointLabel(0, u"\u00B1 " + str(
                    round(self.uncertaintyArray[point_Ijk[2]][point_Ijk[1]][point_Ijk[0]])) + " mm")
                self.markupsNode.SetNthControlPointPosition(0, ras[0], ras[1], ras[2])
                self.markupsNode.GetDisplayNode().SetGlyphSize(
                    round(self.uncertaintyArray[point_Ijk[2]][point_Ijk[1]][point_Ijk[0]]*2, 2))

            except Exception as e:
                pass

    def game_level_changes_text_mode(self, uncertaintyArray, uncertaintyNode, current_level):
        self.uncertaintyArray = uncertaintyArray
        self.uncertaintyNode = uncertaintyNode
        self.current_level = current_level


    #   self.markupsNode.GetDisplayNode().SetViewNodeIDs(["vtkMRMLSliceNodeRed"])

