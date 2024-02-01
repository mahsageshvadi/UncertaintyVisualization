# Updating

import time
import numpy as np
import cv2
# GT

number_of_components =  np.random.randint(1, 3)
black_hole = 1  # np.random.choice([0, 1], p=[0.2, 0.8])

angle_main = 0
ovalImage = np.zeros(shape=(300, 300, 3), dtype= np.uint8)
center_main = (150, 150)
axesLength = (50, 15)
cv2.ellipse(ovalImage, center_main, axesLength, angle_main, 0, 360, (255, 255, 255), -1)

updateVolumeFromArray(gtComponent1, ovalImage)

list_of_angles = []
list_of_ceters = []
list_of_axesLength = []
list_of_angles.append(angle_main)
list_of_ceters.append(center_main)
list_of_axesLength.append(axesLength)

list_of_variation_volumes = []

for i in range(number_of_components):

    angle = np.random.randint(-20, 20)
    list_of_angles.append(angle)

    centerx = np.random.randint(100, 200)
    if i == 0:
        center = (centerx, 150)
    else:
        center = (150, centerx)

    list_of_ceters.append(center)

    axesLength1 = np.random.randint(30, 100)
    axesLength2 = np.random.randint(30, 90)

    axesLength = (axesLength1, axesLength2)
    list_of_axesLength.append(axesLength)

    cv2.ellipse(ovalImage, center, axesLength, angle, 0, 360, (255, 255, 255), -1)
    updateVolumeFromArray(gtComponent2, ovalImage)

if black_hole == 1:
    angle = np.random.randint(0, 360)
    list_of_angles.append(angle)

    centerx = np.random.randint(120, 180)
    center = (centerx, 150)
    list_of_ceters.append(center)

    axesLength1 = np.random.randint(10, 40)
    axesLength2 = np.random.randint(10, 40)

    axesLength = (axesLength1, axesLength2)
    list_of_axesLength.append(axesLength)
# cv2.ellipse(ovalImage, center, axesLength, angle, 0, 220, (0, 0, 0), -1)

#mean = 0
#std = 15
#gaussian_noise = np.random.normal(mean, std, ovalImage.shape)

# Add the noise to the image
#noisy_image = ovalImage + gaussian_noise

# Clip the values to be in the valid range and convert back to uint8
#noisy_image = np.clip(noisy_image, 0, 255)
#noisy_image = np.uint8(noisy_image)
#ovalImage = noisy_image

updateVolumeFromArray(ovalNode, ovalImage)

# Volume 1

number_of_variations = 10

for i in range(number_of_variations):

    # angle_difference = 0
    # if i == 9:
    #	angle_difference = np.random.randint(10,15)

    # else:

    angle_difference = np.random.randint(0, 10)

    angle2 = list_of_angles[0] + angle_difference

    ovalImage2 = np.zeros(shape=(300, 300, 3), dtype=np.uint8)

    center2 = (list_of_ceters[0][0], list_of_ceters[0][1] + np.random.randint(0, 5))

    axesLength2 = list_of_axesLength[0]

    cv2.ellipse(ovalImage2, center2, axesLength2, angle2, 0, 360, (255, 255, 255), -1)

    angle2 = list_of_angles[1]
    center2 = list_of_ceters[1]
    axesLength2 = list_of_axesLength[1]
    cv2.ellipse(ovalImage2, center2, axesLength2, angle2, 0, 360, (255, 255, 255), -1)

    if number_of_components == 1:
        angle2 = list_of_angles[2]
        center2 = list_of_ceters[2]
        axesLength2 = list_of_axesLength[2]

    else:
        angle2 = list_of_angles[3]
        center2 = list_of_ceters[3]
        axesLength2 = list_of_axesLength[3]

    angle_for_black_hole = angle2 + np.random.randint(0, 5)
    center_for_black_hole = (center2[0] + np.random.randint(0, 10), center2[1])
    # cv2.ellipse(ovalImage2, center_for_black_hole, axesLength2, angle_for_black_hole, #0, 360, (0, 0, 0), -1)
   # mean = 0
  #  std = 1
  #  gaussian_noise = np.random.normal(mean, std, ovalImage2.shape)

    # Add the noise to the image
   # noisy_image = ovalImage2 + gaussian_noise

    # Clip the values to be in the valid range and convert back to uint8
   # noisy_image = np.clip(noisy_image, 0, 255)
  #  noisy_image = np.uint8(noisy_image)
   # ovalImage2 = noisy_image

    updateVolumeFromArray(ovalNode2, ovalImage2)
    list_of_variation_volumes.append(ovalImage2)
   # variationNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLScalarVolumeNode')
   # variationNode.SetName("Variation_"+ str(i))
    variationNode = getNode("Variation_"+ str(i))
    updateVolumeFromArray(variationNode, ovalImage2)
    slicer.app.processEvents()
    time.sleep(1)

# STD:

diff_list = []
for i in range(len(list_of_variation_volumes)):
    diff_list.append(list_of_variation_volumes[i] - ovalImage)

diff_stack = np.array(diff_list)
# diff_stack = np.stack([diff1, diff2, diff3])
uncertainty_std = np.std(diff_stack, axis=0)  # Standard deviation

updateVolumeFromArray(uncertaintyNode, uncertainty_std)
