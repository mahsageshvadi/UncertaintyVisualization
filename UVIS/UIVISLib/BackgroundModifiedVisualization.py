import numpy as np
import slicer
import os
from scipy.ndimage import gaussian_filter


class BackgroundModifiedVisualization():

    def __init__(self, uncertainty_array, input_image_array, input_image_node):

        self.BackgroundModifedVisualization = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode",
                                                                                 "BackgroundModifedVisualization")
        imageDirections = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        imageSpacing = [0.5, 0.5, 0.5]
        self.BackgroundModifedVisualization.SetIJKToRASDirections(imageDirections)
        self.BackgroundModifedVisualization.SetSpacing(imageSpacing)

        self.backgroundToBemodified = input_image_array
        self.mainBackground = input_image_node
        self.origin = self.mainBackground.GetOrigin()
        self.BackgroundModifedVisualization.SetOrigin(self.origin)
        self.uncertaintyArray = uncertainty_array

        self.initializeFilteringVariables()
        self.nonBinaryModeInitiation()

    def initializeFilteringVariables(self):

        self.numberOfSections = 2
        self.sigmas = [0, 3]
        self.bluredArrays = []
        self.masks = []
        self.uncertaintyBorders = [self.uncertaintyArray.min(), 4, self.uncertaintyArray.max()]
        self.masked_uncertainty_volumes = []
        self.blured_masked_volumes = []
        self.current_filter_level = 0
        self.current_filter_thershold = round(self.uncertaintyArray.min())
        self.filterType = "Blur"
        self.filteredAllVolumes = {'Blur': np.load('/Users/mahsa/BWH/Silcer/Uncertainty_VIS/Data/FilteredVolumes/FilteredVolumesBlur-filteredVolumes.npy'),
               'Noise': np.load('/Users/mahsa/BWH/Silcer/Uncertainty_VIS/Data/FilteredVolumes'
                                '/FilteredVolumesNoise-filteredVolumes.npy'),
               'Light': np.load('/Users/mahsa/BWH/Silcer/Uncertainty_VIS/Data/FilteredVolumes'
                                '/FilteredVolumesLight-filteredVolumes.npy')}

        self.currentFilteredVolume = self.filteredAllVolumes['Blur'][0][:][:][:]


    def getCurrentAllVolumes(self, filter_type):

        return self.filteredAllVolumes


    def setBlurringVariables(self, sigmas, uncertaintyBorders):

        self.sigmas = sigmas
        self.uncertaintyBorders = uncertaintyBorders

    def setFilterType(self, filter_type):
        self.filterType = filter_type

        self.filteredAllVolumes = self.getCurrentAllVolumes(filter_type)
        self.currentFilteredVolume = self.filteredAllVolumes[filter_type][0][:][:][:]


    def resetBlurringVariables(self):

        self.bluredArrays = []
        self.masks = []
        self.masked_uncertainty_volumes = []
        self.blured_masked_volumes = []


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

    def filter_level_changed(self, filter_level):
        self.current_filter_level = filter_level

        if self.filterType == 'Light':
            self.currentFilteredVolume = (
                    self.filteredAllVolumes[self.filterType][8-(self.current_filter_thershold  -1)][:][:][:])
        else:
            self.currentFilteredVolume = self.filteredAllVolumes[self.filterType][filter_level* 9 + (self.current_filter_thershold-round(self.uncertaintyArray.min() -1))][:][:][:]
        self.visualizeFilteredBackground()

    def filter_threshold_changed(self, filter_threshold):
        self.current_filter_thershold = filter_threshold

        if self.filterType == 'Light':
            self.currentFilteredVolume = (
                    self.filteredAllVolumes[self.filterType][8-(self.current_filter_thershold  -1)][:][:][:])
        else:
            self.currentFilteredVolume = self.filteredAllVolumes[self.filterType][self.current_filter_level* 9 + (self.current_filter_thershold -round(self.uncertaintyArray.min() -1))][:][:][:]
        self.visualizeFilteredBackground()

    def visualizeFilteredBackground(self, sigmas=None, uncertaintyBorders=None, numberOfSections=None):

        if numberOfSections is not None:
            self.numberOfSections = numberOfSections

        slicer.util.updateVolumeFromArray(self.BackgroundModifedVisualization, self.currentFilteredVolume)

        self.resetBlurringVariables()
        slicer.util.setSliceViewerLayers(background=self.BackgroundModifedVisualization)

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


    def turnBluredVisualizationOff(self):

        slicer.util.setSliceViewerLayers(background=self.mainBackground)

