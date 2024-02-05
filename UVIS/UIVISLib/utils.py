import slicer
import re

_Extention_name = 'UVIS'
_filter_types = ['Light', 'Noise', 'Blur']

#
_filter_levels = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

_noise_filter_local_scale = 15
_blur_filter_local_scale = 0.5
_transparency_local_scale = 0.1


def get_noise_filter_local_scale():
    return _noise_filter_local_scale


def get_blur_filter_local_scale(filter_level):
    return 0.5 * (1 + (filter_level * 0.5))


def get_transparency_local_scale():
    return _transparency_local_scale


def get_filter_types():
    return _filter_types


def get_filter_levels():
    return _filter_levels


def get_project_root():
    # c = slicer.util.getModule(_Extention_name).path
    project_main_file_path = 'Users/mahsa/BWH/Silcer/Uncertainty_VIS/UVIS'
    last_slash_index = project_main_file_path.rfind('/')

    return project_main_file_path[:last_slash_index + 1]
