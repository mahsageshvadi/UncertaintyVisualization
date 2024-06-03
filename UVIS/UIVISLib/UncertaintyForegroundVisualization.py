import numpy as np
import slicer
import vtk
import qt


class UncertaintyForegroundVisualization():
    color_overlay_surgeon_centric_mask_margin = 10
    FLICKER_INTERVAL_MS = 400
    # todo Sync this with the slider value
    flicker_initial_threshold = 4

    def __init__(self, uncertaintyNode, input_image_node):

        self.already_in_flicker = None
        self.initialize_color_overlay_surgeon_centric()
        self.initialize_flicker_mode()
        self.input_image_node = input_image_node
        # Node to display uncertainty in this layer
        self.uncertaintyVISVolumeNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode",
                                                                           'Uncertainty_Foreground')
        self.align_volume_based_on_input_node(self.uncertaintyVISVolumeNode, input_image_node)

        self.uncertaintyNode = None
        self.uncertaintyArray = None
        self.lookupTable = None
        self.opacity = None

        self.current_visibility = False
        self.initialize_nodes(uncertaintyNode)
        self.update_foreground_with_uncertainty_array(self.uncertaintyArray)
        self.initiate_uncertainty_vis_volume_node()
        self.displayNode = self.uncertaintyVISVolumeNode.GetDisplayNode()
        self.red_composite_node = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceCompositeNodeRed')
        self.is_color_overlay_active = False

    def align_volume_based_on_input_node(self, volume_node, input_image_node):

        origin = input_image_node.GetOrigin()
        spacing = input_image_node.GetSpacing()
        directionMatrix = vtk.vtkMatrix4x4()
        input_image_node.GetIJKToRASDirectionMatrix(directionMatrix)
        volume_node.SetOrigin(origin)
        volume_node.SetSpacing(spacing)
        volume_node.SetIJKToRASDirectionMatrix(directionMatrix)

    def initialize_color_overlay_surgeon_centric(self):
        self.mask = self.shpere_mask(self.color_overlay_surgeon_centric_mask_margin)
        self.is_color_overlay_surgeon_centric = False

    def initialize_flicker_mode(self):
        self.flicker_timer = qt.QTimer()
        self.flicker_timer.setInterval(self.FLICKER_INTERVAL_MS)
        # Connect the timer to toggle flicker
        self.flicker_timer.timeout.connect(self.toggle_flicker)
        self.flicker_is_enabled = False
        self.flicker_threshold = self.flicker_initial_threshold
        self.already_in_flicker = False

    def initiate_uncertainty_vis_volume_node(self):

        #  self.uncertaintyVISVolumeNode.SetDisplayVisibility(True)
        slicer.util.setSliceViewerLayers(foreground=self.uncertaintyVISVolumeNode, foregroundOpacity=0.0)

    def initialize_nodes(self, uncertaintyNode):

        self.uncertaintyNode = uncertaintyNode
        self.uncertaintyArray = slicer.util.arrayFromVolume(self.uncertaintyNode)

    def set_surgeon_centric_mode(self, surgeonCentricMode):

        self.is_color_overlay_surgeon_centric = surgeonCentricMode

    def enable_color_overlay_foreground(self, is_checked):
        # todo Check if the Filcker mode is on also the color overlay surgeon centric and if each of them are on ask
        #  them to turn it off
        #  change the uncertainty foreground volume to the uncertainty array with the same color map

        self.is_color_overlay_active = is_checked
        self.update_foreground_with_uncertainty_array(self.uncertaintyArray)
        self.align_volume_based_on_input_node(self.uncertaintyVISVolumeNode, self.input_image_node)

        if not is_checked:
            slicer.util.setSliceViewerLayers(foreground=self.uncertaintyVISVolumeNode, foregroundOpacity=0.0)
        else:
            slicer.util.setSliceViewerLayers(foreground=self.uncertaintyVISVolumeNode, foregroundOpacity=0.5)

    def update_foreground_with_uncertainty_array(self, update_array):

       # if self.is_color_overlay_surgeon_centric:
       #     update_array[~self.mask] = 0

        slicer.util.updateVolumeFromArray(self.uncertaintyVISVolumeNode, update_array)

    def shpere_mask(self, radius):

        center = (2, int(radius), int(radius))
        gh = radius * 2
        Y, X, Z = np.ogrid[:1, :gh, :gh]
        dist_from_center = np.sqrt((X - center[0]) ** 2 + (Y - center[1]) ** 2 + (Z - center[1]) ** 2)

        mask = dist_from_center <= radius

        return mask

    def visualize(self, ras=[1.0, 1.0, 1.0], point_Ijk=[0, 0, 0]):

        if self.is_color_overlay_surgeon_centric:

                try:
                    uncertaintyArray_croped = self.surgeon_centric_array_calculation(point_Ijk)
                    self.update_foreground_with_uncertainty_array(uncertaintyArray_croped)
                    slicer.util.setSliceViewerLayers(foreground=self.uncertaintyVISVolumeNode, foregroundOpacity=0.5)

                    #self.uncertaintyVISVolumeNode.SetOrigin(
                      #  [(ras[0] - (self.color_overlay_surgeon_centric_mask_margin / 2)), (ras[1] - (self.color_overlay_surgeon_centric_mask_margin / 2)),
                       #  ras[2]])
                    self.uncertaintyVISVolumeNode.SetOrigin(ras[0], ras[1], ras[2])

                except:
                    pass

        else:

            self.update_foreground_with_uncertainty_array(self.uncertaintyArray)
            self.align_volume_based_on_input_node(self.uncertaintyVISVolumeNode, self.input_image_node)

            if self.is_color_overlay_active is True:
                slicer.util.setSliceViewerLayers(foreground=self.uncertaintyVISVolumeNode, foregroundOpacity=0.5)
            else:
                slicer.util.setSliceViewerLayers(foreground=self.uncertaintyVISVolumeNode, foregroundOpacity=0.0)


    def enable_disable_flicker_mode(self, is_checked):

        self.flicker_is_enabled = is_checked
        if not is_checked:
            self.stop_flicker()
            if self.is_color_overlay_active is True:
                slicer.util.setSliceViewerLayers(foreground=self.uncertaintyVISVolumeNode, foregroundOpacity=0.5)
            else:
                slicer.util.setSliceViewerLayers(foreground=self.uncertaintyVISVolumeNode, foregroundOpacity=0.0)


    def perform_flicker_if_uncertainty_more_than_threshold(self, point_Ijk):
        try:
            if self.flicker_is_enabled:
                if round(self.uncertaintyArray[point_Ijk[2]][point_Ijk[1]][point_Ijk[0]]) > self.flicker_threshold:
                    if not self.already_in_flicker:
                        self.already_in_flicker = True
                        self.start_flicker()
                else:
                    self.stop_flicker()
                    self.already_in_flicker = False

        except Exception as e:
            pass

    # triger toggle flicker with timer
    def start_flicker(self):
        self.flicker_timer.start()

    def stop_flicker(self):
        self.flicker_timer.stop()
        # slicer.util.setSliceViewerLayers(foreground=self.uncertaintyVISVolumeNode, foregroundOpacity=0.5)
        self.current_visibility = False

    #    self.uncertaintyVISVolumeNode.SetOrigin([ras[0]-(color_overlay_surgeon_centric_mask_margin/2), ras[1]-(color_overlay_surgeon_centric_mask_margin/2), ras[2]-(color_overlay_surgeon_centric_mask_margin/2)])

    def toggle_flicker(self):

        if not self.current_visibility:
            slicer.util.setSliceViewerLayers(foreground=self.uncertaintyVISVolumeNode, foregroundOpacity=0.5)
            self.current_visibility = True
        else:
            slicer.util.setSliceViewerLayers(foreground=self.uncertaintyVISVolumeNode, foregroundOpacity=0.0)
            self.current_visibility = False

    def change_flicker_threshold(self, threshold):
        self.flicker_threshold = round(threshold / 100)

    def surgeon_centric_array_calculation(self, point_Ijk):

        lefti = point_Ijk[0] - self.color_overlay_surgeon_centric_mask_margin
        righti = point_Ijk[0] + self.color_overlay_surgeon_centric_mask_margin

        leftj = point_Ijk[1] - self.color_overlay_surgeon_centric_mask_margin
        rigthj = point_Ijk[1] + self.color_overlay_surgeon_centric_mask_margin

        leftk = point_Ijk[2] - self.color_overlay_surgeon_centric_mask_margin
        rightk = point_Ijk[2] + self.color_overlay_surgeon_centric_mask_margin

        if lefti < 0:
            lefti = 0

        if leftj < 0:
            leftj = 0

        if leftk < 0:
            leftk = 0

        uncertainty_array_copy = self.uncertaintyArray.copy()
        uncertainty_array_croped = uncertainty_array_copy[leftk:rightk, leftj:rigthj, lefti:righti]

    #    uncertainty_array_croped = uncertainty_array_croped - self.uncertaintyArray.min()
    #    uncertainty_array_croped = uncertainty_array_croped / (self.uncertaintyArray.max() - self.uncertaintyArray.min())

   #     uncertainty_array_croped = uncertainty_array_croped * 255

        return uncertainty_array_croped

    def apply_initial_threshold_for_color_overlay_display(self, threshold):
        self.displayNode.SetApplyThreshold(1)
        self.displayNode.SetLowerThreshold(threshold)

    def game_level_changes_uncertainty_foreground(self, uncertainty_node, input_image_node):

        self.input_image_node = input_image_node
        self.align_volume_based_on_input_node(self.uncertaintyVISVolumeNode, input_image_node)
        self.initialize_nodes(uncertainty_node)
        self.update_foreground_with_uncertainty_array(self.uncertaintyArray)

        self.red_composite_node.SetForegroundVolumeID(self.uncertaintyVISVolumeNode.GetID())

        if self.is_color_overlay_active:
            self.red_composite_node.SetForegroundOpacity(0.5)

        else:

            self.red_composite_node.SetForegroundOpacity(0.0)
