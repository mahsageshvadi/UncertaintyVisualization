import os
import numpy as np
import nibabel as nib
import UsefulFunctions

from scipy.ndimage import gaussian_filter

class CalculateAllFilters():
    def __init__(self, image_array, uncertainty_array):
        self.image_array = image_array
        self.uncertainty_array = uncertainty_array

    def filter_calculations_initialization(self):
        filterd_volume_path = utilities.get_project_root() + '/Data/FilteredVolumes'
        if not os.path.exists(filterd_volume_path):
            os.makedirs(filterd_volume_path)

        image_array_copy = self.image_array.copy()
        sigma_values = self.generate_sigma_values(1, self.uncertainty_array)
        filter_threshold_max = round(self.uncertainty_array.max()-1)
        filter_threshold_min = round(self.uncertainty_array.min()-1)
        for filter_type in utilities.get_filter_types():
            filtered_volumes_for_file = []
            for filter_level in utilities.get_filter_levels():
                for filter_threshold in range(filter_threshold_min, filter_threshold_max):

                    # get all the filter possibilities with different threshold between
                    # min and max and different filter levels
                    filtered_volume_list, filtered_volume_index_list = self.get_all_filtered_volumes_and_index(
                    filter_type, image_array_copy, sigma_values, filter_level, filter_threshold)
                    # now we have all possibilities then we should assign each sigma uncertainty value with the
                    # corresponding filtered volume
                    final_filtered_volume = self.calculate_final_filtered_volume(self.image_array, sigma_values, filtered_volume_index_list,
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
            if filter_type == "Light":
                filtered_volume_list.append(self.adjust_brightness(image_array_copy, sigma_values.max(), i, filter_threshold))
            elif filter_type == "Noise":
                if i < filter_threshold:
                    filtered_volume_list.append(image_array_copy)
                else:
                    filtered_volume_list.append(self.add_gaussian_noise(image_array_copy, mean=0,
                                                                        std= (i - filter_threshold) * (2.5*filter_level + 2.5)))
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

if __name__ == '__main__':

    image_array_file = nib.load('/Users/mahsa/BWH/Data/ref_ref_t2.nii')
    image_array_data = image_array_file.get_data()

    uncertainty_array_file = nib.load('/Users/mahsa/BWH/Data/gp_uncertainty.nii')
    uncertainty_array_data = uncertainty_array_file.get_fdata()

    calculateAllFiltersClass = CalculateAllFilters(image_array_data, uncertainty_array_data)
    calculateAllFiltersClass.filter_calculations_initialization()