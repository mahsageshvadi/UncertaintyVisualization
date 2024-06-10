import numpy as np
import os
import slicer
import vtk
from scipy.ndimage import gaussian_filter

from UIVISLib.UsefulFunctions import UsefulFunctions

usefulFunctions = UsefulFunctions()


class BackgroundModifiedVisualization():

    def __init__(self, uncertainty_array, input_image_array, input_image_node):

        self.current_filter_threshold = None
        self.filterType = None
        self.mainBackground = input_image_node

        self.BackgroundModifedVisualization = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode",
                                                                                 "BackgroundModifedVisualization")

        self.align_volume_based_on_input_node(self.BackgroundModifedVisualization)
        self.backgroundToBeModified = input_image_array
        self.uncertainty_array = uncertainty_array
        self.filter_types = ['Light', 'Noise', 'Blur']
        self.filter_levels = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        self.levels = {

            '0': 'Case020',
            '1': 'Case015',
            '2': 'Case097',
            '3': 'Case112'
        }

        self.filtered_all_volumes = []

        self.numberOfSections = 2
        self.sigmas = [0, 3]
        self.bluredArrays = []
        self.masks = []
        self.uncertaintyBorders = [self.uncertainty_array.min(), 4, self.uncertainty_array.max()]
        self.masked_uncertainty_volumes = []
        self.blured_masked_volumes = []
        self.current_filter_level = 0
        self.current_filter_threshold = round(self.uncertainty_array.min())
        self.filter_type = "Blur"
     #   self.input_file_name = input_volume_dir.split('/')[-1]
        self.initialize_filtered_volumes()
        self.red_composite_node = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceCompositeNodeRed')
        self.layoutManager = slicer.app.layoutManager()
        # self.non_binary_mode_initiation()

        self.slice_widget_red = self.layoutManager.sliceWidget('Red')
        self.slice_widget_green = self.layoutManager.sliceWidget('Green')
        self.slice_logic_red = self.slice_widget_red.sliceLogic()
        self.slice_logic_green = self.slice_widget_green.sliceLogic()

        self.current_level = 0
        self.current_filtered_volume = self.filtered_all_volumes[self.current_level]['Blur'][0][:][:][:]
        slicer.util.setSliceViewerLayers(background=self.mainBackground)

    def get_slice_view_info(self, sliceLogic):

        zoom_factor = sliceLogic.GetSliceNode().GetFieldOfView()
        center_position = sliceLogic.GetSliceNode().GetXYZOrigin()
        return zoom_factor, center_position

    def set_slice_view_info(self, sliceLogic, zoom_factor, center_position):

        sliceLogic.GetSliceNode().SetFieldOfView(zoom_factor[0], zoom_factor[1], zoom_factor[2])
        sliceLogic.GetSliceNode().SetXYZOrigin(center_position[0], center_position[1], center_position[2])

    def align_volume_based_on_input_node(self, volume_node):

        origin = self.mainBackground.GetOrigin()
        spacing = self.mainBackground.GetSpacing()
        directionMatrix = vtk.vtkMatrix4x4()
        self.mainBackground.GetIJKToRASDirectionMatrix(directionMatrix)
        volume_node.SetOrigin(origin)
        volume_node.SetSpacing(spacing)
        volume_node.SetIJKToRASDirectionMatrix(directionMatrix)

    def initialize_filtered_volumes(self):
        project_root = os.path.dirname(__file__)

        for i in range(len(self.levels)):

            input_file_name = list(self.levels.items())[i][1] + '_0_pred.nii'

            filterd_volume_path = project_root + '/Data/' + input_file_name + '/'
            if os.path.exists(filterd_volume_path):

                self.filtered_all_volumes.append({'Blur': np.load(filterd_volume_path + '/Blur-filteredVolumes.npy'),
                                             'Noise': np.load(filterd_volume_path + '/Noise-filteredVolumes.npy'),
                                             'Light': np.load(filterd_volume_path + '/Light-filteredVolumes.npy')})

            else:
                os.makedirs(filterd_volume_path)
                self.filter_calculations_initialization(filterd_volume_path, i)
                self.initialize_filtered_volumes()

    def filter_calculations_initialization(self, filterd_volume_path, i):

        image_array_copy = self.backgroundToBeModified.copy()
        sigma_values = self.generate_sigma_values(1, self.uncertainty_array)
        filter_threshold_max = round(self.uncertainty_array.max())
        filter_threshold_min = round(self.uncertainty_array.min())
        for filter_type in self.filter_types:
            filtered_volumes_for_file = []
            for filter_level in self.filter_levels:
                for filter_threshold in range(filter_threshold_min, filter_threshold_max):
                    # get all the filter possibilities with different threshold between
                    # min and max and different filter levels
                    filtered_volume_list, filtered_volume_index_list = self.get_all_filtered_volumes_and_index(
                        filter_type, image_array_copy, sigma_values, filter_level, filter_threshold)
                    # now we have all possibilities then we should assign each sigma uncertainty value with the
                    # corresponding filtered volume
                    final_filtered_volume = self.calculate_final_filtered_volume(self.backgroundToBeModified,
                                                                                 sigma_values,
                                                                                 filtered_volume_index_list,
                                                                                 filtered_volume_list)
                    filtered_volumes_for_file.append(final_filtered_volume)

            file_name = filter_type + '-filteredVolumes.npy'
            file_path = filterd_volume_path + file_name
            np.save(file_path, filtered_volumes_for_file)
          #  self.filtered_all_volumes[i][filter_type] = filtered_volumes_for_file

    def generate_sigma_values(self, decimal_place, uncertainty_array):

        return np.round(uncertainty_array, decimal_place)

    def get_all_filtered_volumes_and_index(self, filter_type, image_array_copy, sigma_values, filter_level,
                                           filter_threshold):

        filtered_volume_list = []
        filtered_volume_index_list = []

        for i in np.unique(sigma_values):
            if filter_type == "Light":
                filtered_volume_list.append(
                    self.adjust_brightness(image_array_copy, sigma_values.max(), i, filter_threshold))
            elif filter_type == "Noise":
                if i < filter_threshold:
                    filtered_volume_list.append(image_array_copy)
                else:
                    filtered_volume_list.append(self.add_gaussian_noise(image_array_copy, mean=3,
                                                                        std=(i - filter_threshold) * (
                                                                                    20 * filter_level + 2.5)))
            elif filter_type == "Blur":
                filtered_volume_list.append(gaussian_filter(image_array_copy,
                                                            sigma=(i - filter_threshold) * (0.25 * (filter_level + 1))))

            filtered_volume_index_list.append(i)

        return filtered_volume_list, filtered_volume_index_list

    def calculate_final_filtered_volume(self, image_volume, sigma_values, filtered_volume_index_list,
                                        filtered_volume_list):

        depth, height, width = image_volume.shape
        filtered_volume = np.zeros(shape=(depth, height, width))

        for k in range(depth):
            for j in range(height):
                for i in range(width):
                    sigma_value = sigma_values[k, j, i]
                    index = filtered_volume_index_list.index(sigma_value)
                    filtered_volume[k, j, i] = filtered_volume_list[index][k, j, i]

        return filtered_volume

    def adjust_brightness(self, volume, sigma_max, sigma_value, filter_threshold):

        factor = (sigma_max - sigma_value) / sigma_max
        return (volume * factor) - filter_threshold * 10

    def add_gaussian_noise(self, volume, mean=0, std=1):

        noise = np.random.normal(mean, std, size=volume.shape)
        return volume + noise

    def set_blurring_variables(self, sigmas, uncertaintyBorders):

        self.sigmas = sigmas
        self.uncertaintyBorders = uncertaintyBorders

    def set_filter_type(self, filter_type):

        self.filter_type = filter_type
        self.current_filtered_volume = self.filtered_all_volumes[self.current_level][self.filter_type][
            (self.current_filter_level * round(self.uncertainty_array.max())) + self.current_filter_threshold]
        self.visualize_filtered_background()

    def reset_blurring_variables(self):

        self.bluredArrays = []
        self.masks = []
        self.masked_uncertainty_volumes = []
        self.blured_masked_volumes = []

    def non_binary_mode_initiation(self):

        self.backgroundToBemodifiedCopy = self.backgroundToBeModified.copy()
        self.sigma_values = self.uncertainty_array.copy()
        self.sigma_values = np.round(self.sigma_values, 1)
        max_sigma = np.max(self.sigma_values).astype(int)

        blurred_volume_list = []
        blurred_volume_index_list = []

        for i in np.unique(self.sigma_values):
            blurred_volume_list.append(gaussian_filter(self.backgroundToBemodifiedCopy, sigma=i - 3))
            blurred_volume_index_list.append(i)

        depth, height, width = self.backgroundToBemodifiedCopy.shape
        self.nonBinaryblurredVolume = np.zeros(shape=(depth, height, width))
        nonBinaryblurredVolumeNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")

        for k in range(depth):
            for j in range(height):
                for i in range(width):
                    sigma_value = self.sigma_values[k, j, i]
                    index = blurred_volume_index_list.index(sigma_value)
                    self.nonBinaryblurredVolume[k, j, i] = blurred_volume_list[index][k, j, i]

    def filter_level_changed(self, filter_level):
        self.current_filter_level = filter_level

        if self.filter_type == 'Light':
            self.current_filtered_volume = (
                self.filtered_all_volumes[self.current_level][self.filter_type][8 - (self.current_filter_threshold - 1)][:][:][:])
        else:
            #self.current_filtered_volume = self.filtered_all_volumes[self.filter_type][filter_level * 9 + (
                  #      self.current_filter_threshold - round(self.uncertainty_array.min() - 1))][:][:][:]
            self.current_filtered_volume = self.filtered_all_volumes[self.current_level][self.filter_type][
                (self.current_filter_level *round(self.uncertainty_array.max()))+ self.current_filter_threshold]
            self.visualize_filtered_background()

    def filter_threshold_changed(self, filter_threshold):
        self.current_filter_threshold = filter_threshold
        if self.filter_type == 'Light':
            self.current_filtered_volume = (
                self.filtered_all_volumes[self.current_level][self.filter_type][8 - (self.current_filter_threshold - 1)][:][:][:])
        else:
            self.current_filtered_volume = self.filtered_all_volumes[self.current_level][self.filter_type][
                (self.current_filter_level *round(self.uncertainty_array.max()))+ self.current_filter_threshold]
        self.visualize_filtered_background()

    def visualize_filtered_background(self, sigmas=None):

        zoom_factor, center_position = self.get_slice_view_info(self.slice_logic_red)
        zoom_factor_green, center_position_green = self.get_slice_view_info(self.slice_logic_green)

        slicer.util.updateVolumeFromArray(self.BackgroundModifedVisualization, self.current_filtered_volume)

        self.reset_blurring_variables()
        #slicer.util.setSliceViewerLayers(background=self.BackgroundModifedVisualization)

        self.red_composite_node.SetBackgroundVolumeID(self.BackgroundModifedVisualization.GetID())
        self.slice_widget_red.fitSliceToBackground()
        self.set_slice_view_info(self.slice_logic_red, zoom_factor, center_position)
        self.set_slice_view_info(self.slice_logic_green, zoom_factor_green, center_position_green)


    """
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
        # Excluding the infinity mode
        if self.numberOfSections == 12:
            self.bluredFinalVolumeArray = self.nonBinaryblurredVolume

        slicer.util.updateVolumeFromArray(self.BackgroundModifedVisualization, self.bluredFinalVolumeArray)

    """

    def turn_blured_visualization_off(self):

        self.red_composite_node.SetBackgroundVolumeID(self.mainBackground.GetID())

      #  slicer.util.setSliceViewerLayers(background=self.mainBackground)

    def get_current_filtered_node(self):

        return self.BackgroundModifedVisualization

    def get_current_filtered_volume(self):

        return self.current_filtered_volume

    def game_level_changes_background_modified(self, uncertainty_array, input_image_node, level):

        self.current_level = level
        self.uncertainty_array = uncertainty_array
        self.backgroundToBeModified = slicer.util.arrayFromVolume(input_image_node)
        self.mainBackground = input_image_node
        self.align_volume_based_on_input_node(self.BackgroundModifedVisualization)

        self.uncertaintyBorders = [self.uncertainty_array.min(), 4, self.uncertainty_array.max()]
      #  input_file_name = list(self.levels.items())[level][1] +'_0_pred.nii'
      #  self.initialize_filtered_volumes()

        if self.filter_type == 'Light':
            self.current_filtered_volume = (
                self.filtered_all_volumes[self.current_level][self.filter_type][8 - (self.current_filter_threshold - 1)][:][:][:])
        else:
            self.current_filtered_volume = self.filtered_all_volumes[self.current_level][self.filter_type][
                (self.current_filter_level *round(self.uncertainty_array.max()))+ self.current_filter_threshold]
     #   self.visualize_filtered_background()
