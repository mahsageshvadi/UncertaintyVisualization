import math
import enum
import slicer
import vtk
import numpy as np
class Button(enum.Enum):
    One = 1
    Two = 2
    TumorBigger = 3
    Tumor = 4
    TumorSmaller = 5

class TumorBasedVis():

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

            self.surface_mode_display_node.SetSliceIntersectionThickness(width)

        elif Button == Button.TumorSmaller:

            self.smaller_mode_display_node.SetSliceIntersectionThickness(width)





    def getUnitVec(self, normal):

        normal_magnitude = math.sqrt(sum(n**2 for n in normal))

        return [n / normal_magnitude for n in normal]