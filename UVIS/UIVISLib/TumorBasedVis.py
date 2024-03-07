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

    def __init__(self, uncertainty_array, segmentation_node):

        self.tumor_3D_model_node = None

        self.modelPolyData = None

        self.smaller_mode_display_node = None
        self.larger_model_display_node = None
        self.tumor_3D_model_display_node = None

        self.volumeRasToIjk = None
        self.surface_model_threshold = 0.5
        self.surface_model_smoth = 30
        self.surface_model_decimate = 0.5
        self.uncertainty_array = uncertainty_array

        self.points = None
        self.point_data = None
        self.normals = None

        # self.temporary_init()
        #  self.calculate_uncertatinty_volumes()
        self.segmentation_node = segmentation_node
        self.tumor_3D_model_node = None
        self.larger_model = None
        self.smaller_model = None
        self.generate_tumor_3_d_model()
        self.generate_offsets()

    def test_new_offset_generation(self):
        label_map_volume_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLabelMapVolumeNode', 'LabelMap')

        # Step 4: Convert the segmentation to a label map
        slicer.modules.segmentations.logic().ExportVisibleSegmentsToLabelmapNode(self.segmentation_node,
                                                                                 label_map_volume_node)

        pass

    def generate_tumor_3_d_model(self):

        sh_node = slicer.mrmlScene.GetSubjectHierarchyNode()
        export_folder_item_id = sh_node.CreateFolderItem(sh_node.GetSceneItemID(), "Segments")
        slicer.modules.segmentations.logic().ExportAllSegmentsToModels(self.segmentation_node, export_folder_item_id)
        child_item_ids = vtk.vtkIdList()
        sh_node.GetItemChildren(export_folder_item_id, child_item_ids, True)
        for i in range(child_item_ids.GetNumberOfIds()):
            item_id = child_item_ids.GetId(i)
            data_node = sh_node.GetItemDataNode(item_id)
            if data_node:
                if data_node.IsA("vtkMRMLModelNode"):
                    new_name = "Tumor_3D_model".format(i)
                    data_node.SetName(new_name)
                    self.tumor_3D_model_node = self.clone_3D_model_node("Tumor_3D_model", data_node)
                    self.tumor_3D_model_display_node = self.tumor_3D_model_node.GetDisplayNode()

                    self.larger_model = self.clone_3D_model_node("Tumor_3D_model_bigger_offset", data_node)
                    self.larger_mode_display_node = self.larger_model.GetDisplayNode()

                    self.smaller_model = self.clone_3D_model_node("Tumor_3D_model_smaller_offset", data_node)
                    self.smaller_mode_display_node = self.smaller_model.GetDisplayNode()

                    slicer.mrmlScene.RemoveNode(data_node)

    def clone_3D_model_node(self, name, originalModelNode):

        cloned_node = slicer.vtkMRMLModelNode()
        cloned_node.Copy(originalModelNode)

        if originalModelNode.GetPolyData():
            cloned_poly_data = vtk.vtkPolyData()
            cloned_poly_data.DeepCopy(originalModelNode.GetPolyData())
            cloned_node.SetAndObservePolyData(cloned_poly_data)
        cloned_node.SetName(name)
        slicer.mrmlScene.AddNode(cloned_node)

        original_display_node = originalModelNode.GetDisplayNode()
        if original_display_node:
            cloned_display_node = slicer.vtkMRMLModelDisplayNode()
            cloned_display_node.Copy(original_display_node)
            slicer.mrmlScene.AddNode(cloned_display_node)
            cloned_node.SetAndObserveDisplayNodeID(cloned_display_node.GetID())

        return cloned_node

    def generate_offsets(self):
        tumor_model_poly_data = self.tumor_3D_model_node.GetPolyData()
        bigger_offset_poly_data = self.larger_model.GetPolyData()
        smaller_offset_poly_data = self.smaller_model.GetPolyData()

        list_of_ras_points_bigger_vol = []
        list_of_ras_points_smaller_vol = []

        points = tumor_model_poly_data.GetPoints()
        point_data = tumor_model_poly_data.GetPointData()
        normals = point_data.GetNormals()

        num_points = points.GetNumberOfPoints()

        model_output_points = bigger_offset_poly_data.GetPoints()
        model_output_points_small = smaller_offset_poly_data.GetPoints()
        volume_ras_to_ijk = vtk.vtkMatrix4x4()

        # todo: change this
       # label_map_volume_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLabelMapVolumeNode', 'LabelMap')
       # slicer.modules.segmentations.logic().ExportVisibleSegmentsToLabelmapNode(self.segmentation_node, label_map_volume_node)
        bigOffNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLScalarVolumeNode', 'NewScalarVolume')
       # volumes_logic = slicer.modules.volumes.logic()
       # volumes_logic.CreateScalarVolumeFromVolume(slicer.mrmlScene, scalar_volume_node, label_map_volume_node)

        bigoff = np.zeros(shape = (self.uncertainty_array.shape[0], self.uncertainty_array.shape[1], self.uncertainty_array.shape[2]))


        print(num_points)
        counter = 0
        for i in range(num_points):

            # Get ith point
            point = [0.0, 0.0, 0.0]
            points.GetPoint(i, point)

            if 1 == 0:
                markups_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
                markups_node.AddControlPoint([0, 0, 0])
                markups_node.SetDisplayVisibility(True)
                markups_node.GetDisplayNode().SetTextScale(0)
                markups_node.GetDisplayNode().SetSelectedColor(1, 0, 0)
                markups_node.GetDisplayNode().SetActiveColor(1, 0, 0)
                markups_node.GetDisplayNode().SetUseGlyphScale(0)
                markups_node.GetDisplayNode().SetGlyphSize(0.1)
                markups_node.SetNthControlPointPosition(0, point[2], point[1], point[0])

            # Get ijk of ith point
            point_Ijk = [0, 0, 0, 1]
            volume_ras_to_ijk.MultiplyPoint(np.append(point, 1.0), point_Ijk)
            point_Ijk = [int(round(c)) for c in point_Ijk[0:3]]

            # Get uncertainty Value of ith point
            uncertainty_value = self.uncertainty_array[point_Ijk[2]][point_Ijk[1]][point_Ijk[0]] / 2

            if counter % 100 == 0:
                print("Hiiii")
                mask  = self.create_sphere_mask(self.uncertainty_array.shape,(point_Ijk[2], point_Ijk[1], point_Ijk[0]), uncertainty_value * 100)
                bigoff[~mask] = 1

            counter += 1
            # Apply the mask within the bounding box in the bigoff array

            # Get normal of ith point
            normal = [0.0, 0.0, 0.0]
            normals.GetTuple(i, normal)

            # Get unit_vect
            unit_vec = self.get_unit_vec(normal)

            # new point for bigger volume
            new_distance = [uncertainty_value * v for v in unit_vec]
            new_point_bigger = [p + d for p, d in zip(point, new_distance)]
            list_of_ras_points_bigger_vol.append(new_point_bigger)
            model_output_points.SetPoint(i, new_point_bigger)

            # new point for smaller volume
            flipped_unit_vec = [-v for v in unit_vec]
            new_distance_smaller = [uncertainty_value * v for v in flipped_unit_vec]
            new_point_smaller = [p2 + d2 for p2, d2 in zip(point, new_distance_smaller)]
            list_of_ras_points_smaller_vol.append(new_point_smaller)

            model_output_points_small.SetPoint(i, new_point_smaller)

        slicer.util.updateVolumeFromArray(bigOffNode, bigoff)

        smaller_offset_poly_data.GetPoints().Modified()

        bigger_offset_poly_data.GetPoints().Modified()
        # modelOutputPoly.Modified()

        slicer.app.processEvents()

    def create_sphere_mask(self, mask_size, center, radius):

        a, b, c = center

        # Create a meshgrid of indices
        x, y, z = np.indices(mask_size)

        # Calculate the distance from the center for each point
        distances = np.sqrt((x - a) ** 2 + (y - b) ** 2 + (z - c) ** 2)

        # Define the sphere: points within a distance r from the center
        sphere_mask = distances <= radius

        return sphere_mask

    def get_unit_vec(self, normal):

        normal_magnitude = math.sqrt(sum(n ** 2 for n in normal))

        return [n / normal_magnitude for n in normal]

    # todo: change it
    def temporary_init(self):

        self.larger_model = slicer.util.getNode('Output4')
        self.larger_mode_display_node = self.larger_model.GetDisplayNode()
        self.modelOutputPoly = self.larger_model.GetPolyData()

        self.smaller_model = slicer.util.getNode('Output5')
        self.smaller_mode_display_node = self.smaller_model.GetDisplayNode()
        self.modelOutputPoly_small = self.smaller_model.GetPolyData()

        self.tumor_3D_model_node = slicer.util.getNode('Output3')
        self.tumor_3D_model_display_node = self.tumor_3D_model_node.GetDisplayNode()

        self.modelPolyData = self.tumor_3D_model_node.GetPolyData()

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
            self.larger_mode_display_node.SetVisibility2D(True)

            self.tumor_3D_model_display_node.VisibilityOn()
            self.tumor_3D_model_display_node.SetVisibility2D(True)

            self.smaller_mode_display_node.VisibilityOn()
            self.smaller_mode_display_node.SetVisibility2D(True)

        else:

            self.larger_mode_display_node.VisibilityOff()
            self.larger_mode_display_node.SetVisibility2D(False)

            self.tumor_3D_model_display_node.VisibilityOff()
            self.tumor_3D_model_display_node.SetVisibility2D(False)

            self.smaller_mode_display_node.VisibilityOff()
            self.smaller_mode_display_node.SetVisibility2D(False)

    def change_opacity_for_tumor_boundries(self, Button, opacity):

        if Button == Button.TumorBigger:

            self.larger_mode_display_node.SetOpacity(opacity / 100)
            self.larger_mode_display_node.SetSliceIntersectionOpacity(opacity / 100)

        elif Button == Button.Tumor:

            self.tumor_3D_model_display_node.SetOpacity(opacity / 100)
            self.tumor_3D_model_display_node.SetSliceIntersectionOpacity(opacity / 100)

        elif Button == Button.TumorSmaller:

            self.smaller_mode_display_node.SetOpacity(opacity / 100)
            self.smaller_mode_display_node.SetSliceIntersectionOpacity(opacity / 100)

    def set_color(self, Button, color):

        color = tuple(c / 255 for c in color)

        if Button == Button.TumorBigger:

            self.larger_mode_display_node.SetColor(color)

        elif Button == Button.Tumor:

            self.tumor_3D_model_display_node.SetColor(color)

        elif Button == Button.TumorSmaller:

            self.smaller_mode_display_node.SetColor(color)

    def set_line_width(self, Button, width):

        if Button == Button.TumorBigger:

            self.larger_mode_display_node.SetSliceIntersectionThickness(width)

        elif Button == Button.Tumor:

            self.tumor_3D_model_display_node.SetSliceIntersectionThickness(width)

        elif Button == Button.TumorSmaller:

            self.smaller_mode_display_node.SetSliceIntersectionThickness(width)
