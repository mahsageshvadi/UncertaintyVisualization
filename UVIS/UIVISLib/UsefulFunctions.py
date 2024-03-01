
class UsefulFunctions():

    def __init__(self):
        self._Extention_name = 'UVIS'
        self._filter_types = ['Light', 'Noise', 'Blur']

        self.volume_size_for_the_game = 300
                #
        self._filter_levels = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

        self._noise_filter_local_scale = 15
        self._blur_filter_local_scale = 0.5
        self._transparency_local_scale = 0.1
        self.origin = (0, 0, 0)
        self.spacing = (0.5, 0.5, 0.5)
        self.directionMatrix  = [[1, 0, 0],
                           [0, 1, 0],
                           [0, 0, 1]]

    def get_noise_filter_local_scale(self):
            return self._noise_filter_local_scale

    def get_blur_filter_local_scale(self, filter_level):
            return 0.5 * (1 + (filter_level * 0.5))

    def get_transparency_local_scale(self):
            return self._transparency_local_scale

    def get_filter_types(self):
            return self._filter_types

    def get_filter_levels(self):
            return self._filter_levels

    def get_project_root(self):
            # c = slicer.util.getModule(_Extention_name).path
            project_main_file_path = 'Users/mahsa/BWH/Silcer/Uncertainty_VIS/UVIS'
            last_slash_index = project_main_file_path.rfind('/')

            return project_main_file_path[:last_slash_index + 1]

    def get_volume_size_for_the_game(self):

            return self.volume_size_for_the_game

    def get_center(self):
            return self.origin

    def get_level_one_ground_truth(self):

            level_one_ground_truth_data = [
                {
                    "angle" : 0,
                    "center" : (150, 150),
                    "axesLength" : (30, 20)
                },
                {
                    "angle": -13,
                    "center": (162, 150),
                    "axesLength": (20, 36)

                },

                {
                    "angle": 15,
                    "center": (150, 145),
                    "axesLength": (28, 25)

                },

                {
                    "angle": 8,
                    "center": (150, 152),
                    "axesLength": (24, 28)

                }

            ]
            return level_one_ground_truth_data

    def align_volumes( self, volume_node):
            self.volume_node.SetSpacing(self.spacing)
            self.volume_node.SetOrigin(self.origin)
            self.volume_node.SetIJKToRASDirections(self.directionMatrix[0][0], self.directionMatrix[0][1], self.directionMatrix[0][2],
                                             self.directionMatrix[1][0], self.directionMatrix[1][1], self.directionMatrix[1][2],
                                             self.directionMatrix[2][0], self.directionMatrix[2][1], self.directionMatrix[2][2])

    def set_origin(self, volume_node):
            volume_node.SetOrigin(self.origin)

