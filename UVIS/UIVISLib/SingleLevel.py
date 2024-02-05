# Updating

import time
import numpy as np
import cv2
# GT

angle_main = 0
ovalImage = np.zeros(shape=(300, 300, 3), dtype= np.uint8)
center_main = (150, 150)
axesLength = (30, 20)
cv2.ellipse(ovalImage, center_main, axesLength, angle_main, 0, 360, (255, 255, 255), -1)

updateVolumeFromArray(gtComponent1, ovalImage)

list_of_angles = []
list_of_ceters = []
list_of_axesLength = []
list_of_angles.append(angle_main)
list_of_ceters.append(center_main)
list_of_axesLength.append(axesLength)

list_of_variation_volumes = []
max_offset_volume = np.zeros(shape=(300, 300, 3), dtype= np.uint8)
min_offset_volume = np.zeros(shape=(300, 300, 3), dtype= np.uint8)
average_offset_volume = np.zeros(shape=(300, 300, 3), dtype= np.uint8)

angle = -13 #np.random.randint(-20, 20)
list_of_angles.append(angle)
center = (162, 150)
list_of_ceters.append(center)
axesLength = (20, 36)
list_of_axesLength.append(axesLength)
cv2.ellipse(ovalImage, center, axesLength, angle, 0, 360, (255, 255, 255), -1)

angle = 15 #np.random.randint(-20, 20)
list_of_angles.append(angle)
center = (150, 145)
list_of_ceters.append(center)
axesLength = (28, 25)
list_of_axesLength.append(axesLength)
cv2.ellipse(ovalImage, center, axesLength, angle, 0, 360, (255, 255, 255), -1)


angle = 8 #np.random.randint(-20, 20)
list_of_angles.append(angle)
center = (150, 152)
list_of_ceters.append(center)
axesLength = (24, 28)
list_of_axesLength.append(axesLength)
cv2.ellipse(ovalImage, center, axesLength, angle, 0, 360, (255, 255, 255), -1)

updateVolumeFromArray(gtComponent2, ovalImage)

#angle = 263 #np.random.randint(0, 360)
#list_of_angles.append(angle)

#center = (174, 150)
#list_of_ceters.append(center)

#axesLength = (3, 2)
#list_of_axesLength.append(axesLength)
#cv2.ellipse(ovalImage, center, axesLength, angle, 0, 220, (0, 0, 0), -1)

updateVolumeFromArray(ovalNode, ovalImage)

# Volume 1

number_of_variations = 50

for i in range(number_of_variations):

    ovalImage2 = np.zeros(shape=(300, 300, 3), dtype=np.uint8)

    angle_difference = np.random.randint(0, 30)
    angle2 = list_of_angles[0] + angle_difference
    center2 = (list_of_ceters[0][0], list_of_ceters[0][1] + np.random.randint(-5, 5))
    axesLength2 = list_of_axesLength[0]
    cv2.ellipse(ovalImage2, center2, axesLength2, angle2, 0, 360, (255, 255, 255), -1)

    angle_difference = np.random.randint(0, 30)
    angle2 = list_of_angles[1] + angle_difference
    center2 = (list_of_ceters[1][0], list_of_ceters[1][1] + np.random.randint(-5, 5))
    axesLength2 = list_of_axesLength[1]
    cv2.ellipse(ovalImage2, center2, axesLength2, angle2, 0, 360, (255, 255, 255), -1)

    angle_difference = np.random.randint(0, 30)
    angle2 = list_of_angles[2]+ angle_difference
    center2 =  (list_of_ceters[2][0], list_of_ceters[2][1] + np.random.randint(-5, 5))
    axesLength2 = list_of_axesLength[2]
    cv2.ellipse(ovalImage2, center2, axesLength2, angle2, 0, 360, (255, 255, 255), -1)


    angle_difference = np.random.randint(0, 30)
    angle2 = list_of_angles[3]+ angle_difference
    center2 = (list_of_ceters[3][0], list_of_ceters[3][1] + np.random.randint(-5, 5))
    axesLength2 = list_of_axesLength[3]
    cv2.ellipse(ovalImage2, center2, axesLength2, angle2, 0, 360, (255, 255, 255), -1)


    if number_of_components == 1:
        angle2 = list_of_angles[2]
        center2 = list_of_ceters[2]
        axesLength2 = list_of_axesLength[2]

    else:
        angle2 = list_of_angles[3]
        center2 = list_of_ceters[3]
        axesLength2 = list_of_axesLength[3]

   # angle_for_black_hole = list_of_angles[4]

  #  center_for_black_hole = (center2[4] , center2[4])
  #  cv2.ellipse(ovalImage2, center_for_black_hole, list_of_axesLength, angle_for_black_hole, 0, 360, (0, 0, 0), -1)


    #todo if you want to add noise, you should change this
    updateVolumeFromArray(ovalNode2, ovalImage2)
    max_offset_volume += ovalImage2
    if i == 0:
        min_offset_volume = ovalImage2
    else:
        min_offset_volume = np.logical_and(temp_for_min_offset == 255, ovalImage2 == 255)
        min_offset_volume = min_offset_volume.astype(np.int32) * 255


    temp_for_min_offset = ovalImage2
    list_of_variation_volumes.append(ovalImage2)
   # variationNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLScalarVolumeNode')
   # variationNode.SetName("Variation_"+ str(i))
    variationNode = getNode("Variation_"+ str(i%10))
    updateVolumeFromArray(variationNode, ovalImage2)
    slicer.app.processEvents()
    time.sleep(0.2)

# STD:

import numpy as np

diff_list = []
for i in range(len(list_of_variation_volumes)):
    diff_list.append(list_of_variation_volumes[i] - ovalImage)

diff_stack = np.array(diff_list)
uncertainty_variance = np.var(diff_stack, axis=0)
updateVolumeFromArray(uncertaintyNode, uncertainty_variance)



#max_offset_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLScalarVolumeNode')
#max_offset_node.SetName("MaxOffset")
updateVolumeFromArray(max_offset_node, max_offset_volume)

min_offset_volume = np.logical_and(min_offset_volume == 255, ovalImage == 255).astype(np.uint8) * 255


#min_offset_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLScalarVolumeNode')
#min_offset_node.SetName("MinOffset")
updateVolumeFromArray(min_offset_node, min_offset_volume)


#average_offset_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLScalarVolumeNode')
#average_offset_node.SetName("Average")
#average_offset_volume = max_offset_volume/ number_of_variations
updateVolumeFromArray(average_offset_node, average_offset_volume)