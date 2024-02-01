s1_node = getNode('Segmentation_1')
s1_array = array('Segmentation_1')

s2_node = getNode('Segmentation_2')
s2_array = array('Segmentation_2')

s3_node = getNode('Segmentation_3')
s3_array = array('Segmentation_3')

uncertainty_array = np.std(np.stack((s1_array, s2_array, s3_array)), axis=0)

#segmenation_uncertainty_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLScalarVolumeNode')
#segmenation_uncertainty_node.SetName("SegmentationUncertainty")

updateVolumeFromArray(segmenation_uncertainty_node, uncertainty_array)


max_offset_volume = np.zeros(shape=(300, 300, 3), dtype= np.uint8)
min_offset_volume = np.zeros(shape=(300, 300, 3), dtype= np.uint8)


max_offset_volume = s1_array + s2_array + s3_array
max_offset_volume = np.clip(max_offset_volume, 0, 255)


temp_result = np.logical_and(s1_array, s2_array)
min_offset_volume = np.logical_and(temp_result, s3_array)
min_offset_volume = min_offset_volume.astype(np.int32) * 255

#max_offset_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLScalarVolumeNode')
#max_offset_node.SetName("Segmentation_MaxOffset")
updateVolumeFromArray(max_offset_node, max_offset_volume)


#min_offset_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLScalarVolumeNode')
#min_offset_node.SetName("Segmentation_MinOffset")
updateVolumeFromArray(min_offset_node, min_offset_volume)

