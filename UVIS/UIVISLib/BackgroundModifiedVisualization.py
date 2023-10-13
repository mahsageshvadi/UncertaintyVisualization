import numpy as np
import slicer
#import utils
import os
from scipy.ndimage import gaussian_filter


class BackgroundModifiedVisualization():

    def __init__(self, uncertaintyArray):

        self.BackgroundModifedVisualization = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode",
                                                                                 "BackgroundModifedVisualization")
        imageDirections = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
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
        self.nonBinaryModeInitiation()

    def initializeBluringVariables(self):

        self.numberOfSections = 2
        self.sigmas = [0, 3]
        self.bluredArrays = []
        self.masks = []
        self.uncertaintyBorders = [self.uncertaintyArray.min(), 4, self.uncertaintyArray.max()]
        self.masked_uncertainty_volumes = []
        self.blured_masked_volumes = []

    def setBlurringVariables(self, sigmas, uncertaintyBorders):

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



    def nonBinaryModeInitiation(self):

        self.backgroundToBemodifiedCopy = self.backgroundToBemodified.copy()
        self.sigma_values = self.uncertaintyArray.copy()
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

    def visualizeBluredBackground(self, sigmas=None, uncertaintyBorders=None, numberOfSections=None):

        if numberOfSections is not None:
            self.numberOfSections = numberOfSections
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
        sigma_values = self.uncertaintyArray
        original_volume = slicer.util.array('ref_ref_t2')
        brain_volume = original_volume.copy()

        sigma_values = np.round(sigma_values, 1)
        max_sigma = np.max(sigma_values).astype(int)

        blurred_volume_list = []
        blurred_volume_index_list = []

        for i in np.unique(sigma_values):
            if self.filterType == "Light":
                blurred_volume_list.append(self.adjust_brightness(brain_volume, sigma_values.max() / 10 - i / 10))
            elif self.filterType == "Noise":
                blurred_volume_list.append(
                    self.add_gaussian_noise(brain_volume, mean=0, std=i * 15 - sigma_values.min() * 15))
            elif self.filterType == "Blur":
                blurred_volume_list.append(gaussian_filter(brain_volume, sigma=i * 1.5 - 5))

            blurred_volume_index_list.append(i)

        depth, height, width = brain_volume.shape
        blurred_volume = np.zeros(shape=(depth, height, width))
        # volumeNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")

        for k in range(depth):
            for j in range(height):
                for i in range(width):
                    sigma_value = sigma_values[k, j, i]
                    index = blurred_volume_index_list.index(sigma_value)
                    blurred_volume[k, j, i] = blurred_volume_list[index][k, j, i]

        slicer.util.updateVolumeFromArray(self.BackgroundModifedVisualization, blurred_volume)

        self.resetBlurringVariables()
        slicer.util.setSliceViewerLayers(background=self.BackgroundModifedVisualization)

    def turnBluredVisualizationOff(self):

        slicer.util.setSliceViewerLayers(background=self.mainBackground)

class CalculateAllFilters():
    def filter_calculations_initialization(self, image_array, uncertainty_array):

        filterd_volume_path = utils.get_project_root() + '/Data/FilteredVolumes'
        if not os.path.exists(filterd_volume_path):
            os.makedirs(filterd_volume_path)

        image_array_copy = image_array.copy()
        sigma_values = self.generate_sigma_values(1, uncertainty_array)
        filter_start_from_zero_threshold_max = round(uncertainty_array.max()-1)
        for filter_type in utils.get_filter_types():
            filtered_volumes_for_file = []
            for filter_level in utils.get_filter_levels():
                for filter_start_from_zero_threshold in range(filter_start_from_zero_threshold_max):
                    filtered_volume_list, filtered_volume_index_list = self.get_all_filtered_volumes_and_index(
                    filter_type,image_array_copy, sigma_values, filter_level, filter_start_from_zero_threshold)
                    final_filtered_volume = self.calculate_final_filtered_volume(image_array, sigma_values, filtered_volume_index_list,
                                        filtered_volume_list)
                    filtered_volumes_for_file.append(final_filtered_volume)
            file_name = filter_type + '-filteredVolumes.npy'
            file_path = filterd_volume_path + file_name
            np.save(file_path, filtered_volumes_for_file)

    def generate_sigma_values(self, decimal_place, uncertainty_array):

        return np.round(uncertainty_array, decimal_place)

    def get_all_filtered_volumes_and_index(self, filter_type, image_array_copy, sigma_values, filter_level,
                                           filter_threshold):

        filtered_volume_list = []
        filtered_volume_index_list = []

        for i in np.unique(sigma_values):

            filtered_volume_list.append(gaussian_filter(image_array_copy, sigma=i * filter_level -
                                                                                filter_threshold))
            for i in np.unique(sigma_values):
                if filter_type == "Light":
                    local_scale = utils.get_transparency_local_scale() * filter_level
                    filtered_volume_list.append(self.adjust_brightness(image_array_copy, sigma_values.max() , i , filter_threshold))
                elif filter_type == "Noise":
                    if i < filter_threshold:
                        filtered_volume_list.append(image_array_copy)
                    else:
                        filtered_volume_list.append(self.add_gaussian_noise(image_array_copy, mean=0, std= (i - filter_threshold) * (2.5*filter_level + 2.5)))

                elif filter_type == "Blur":
                    filtered_volume_list.append(gaussian_filter(image_array_copy,
                                                                sigma=(i - filter_threshold) *(0.25 * (filter_level + 1))))

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
