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

