import slicer



userSeesGoldKaleNode = getNode('Variation_0')
userSeesGoldKaleVolume = array('Variation_0')
userSeesGoldKaleVolumeTemp = userSeesGoldKaleVolume.copy()
goldKaleSize = userSeesGoldKaleVolume.shape


userSeesMapVolume = userSeesVolume.copy()

userSeesMapVolume = np.where(userSeesMapVolume == 255, 1, -1)


gtNode = getNode('GroundTruth')
gtVolume = array('GroundTruth')

gtMapVolume = gtVolume.copy()

gtMapVolume = np.where(gtMapVolume == 255, 1, -1)



totalScoreTextNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
totalScoreTextNode.SetName("totalScoreTextNode")

totalScoreTextNode.AddControlPoint([0,0,0])
totalScoreTextNode.GetDisplayNode().SetUseGlyphScale(0)
totalScoreTextNode.GetDisplayNode().SetGlyphType(3)
totalScoreTextNode.GetDisplayNode().SetSelectedColor(0,0,0)
totalScoreTextNode.GetDisplayNode().SetActiveColor(0,0,0)
totalScoreTextNode.GetDisplayNode().SetTextScale(3.5)
totalScoreTextNode.SetNthControlPointLabel(0, "$ 0")
totalScoreTextNode.SetNthControlPointPosition(0, -2900, -950, 0)


scoreTextNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
scoreTextNode.SetName("scoreTextNode")

scoreTextNode.AddControlPoint([0,0,0])
#scoreTextNode.SetDisplayVisibility(False)
scoreTextNode.GetDisplayNode().SetGlyphType(6)
scoreTextNode.GetDisplayNode().SetSelectedColor(0,0,0)
scoreTextNode.GetDisplayNode().SetActiveColor(0,0,0)
scoreTextNode.GetDisplayNode().SetTextScale(4)
scoreTextNode.GetDisplayNode().SetOpacity(0.7)
scoreTextNode.GetDisplayNode().SetGlyphSize(4)


uncertaintyTextNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
uncertaintyTextNode.SetName("UncertaintyTextNode")

uncertaintyTextNode.AddControlPoint([0,0,0])
uncertaintyTextNode.SetDisplayVisibility(False)
uncertaintyTextNode.GetDisplayNode().SetGlyphType(6)
uncertaintyTextNode.GetDisplayNode().SetSelectedColor(0,1,0)
uncertaintyTextNode.GetDisplayNode().SetActiveColor(0,1,0)
uncertaintyTextNode.GetDisplayNode().SetTextScale(4)
uncertaintyTextNode.GetDisplayNode().SetOpacity(0.7)
uncertaintyTextNode.GetDisplayNode().SetGlyphSize(4)



def reset():
    crosshairNode.RemoveAllObservers()
    updateVolumeFromArray(userSeesGoldKaleNode, userSeesGoldKaleVolumeTemp)
    global userSeesGoldKaleVolume
    userSeesGoldKaleVolume = userSeesGoldKaleVolumeTemp.copy()
    global totalScore
    totalScore = 0
    totalScoreTextNode.SetNthControlPointLabel(0, "$ " + str(totalScore))


def onMouseMoved(observer, eventid):
    global isGainingScoreStarted
    global totalScore
    global userSeesGoldKaleVolume

    ras = [1.0, 1.0, 1.0]

    crosshairNode.GetCursorPositionRAS(ras)
    volumeRasToIjk = vtk.vtkMatrix4x4()
    userSeesGoldKaleNode.GetRASToIJKMatrix(volumeRasToIjk)

    point_Ijk = [0, 0, 0, 1]
    volumeRasToIjk.MultiplyPoint(np.append(ras, 1.0), point_Ijk)
    point_Ijk = [int(round(c)) for c in point_Ijk[0:3]]
    radius = 5
    z_range = range(max(0, point_Ijk[2] - radius), min(userSeesGoldKaleVolume.shape[0], point_Ijk[2] + radius + 1))
    y_range = range(max(0, point_Ijk[1] - radius), min(userSeesGoldKaleVolume.shape[1], point_Ijk[1] + radius + 1))
    x_range = range(max(0, point_Ijk[0] - radius), min(userSeesGoldKaleVolume.shape[2], point_Ijk[0] + radius + 1))

    score = 0
    for z in z_range:
        for y in y_range:
            for x in x_range:
                if (x - point_Ijk[0]) ** 2 + (y - point_Ijk[1]) ** 2 + (z - point_Ijk[2]) ** 2 <= radius ** 2:
                    userSeesGoldKaleVolume[z, y, x] = 0.0
                    if not mindedPoints[z, y, x]:
                        mindedPoints[z, y, x] = 1
                        tempScore = calculate_score_for(gtMapVolume[z, y, x], userSeesMapVolume[z, y, x]) / 1000
                        if tempScore > 0:
                            isGainingScoreStarted = True
                        if tempScore < 0 and isGainingScoreStarted:
                            scoreTextNode.GetDisplayNode().SetTextScale(5)
                            scoreTextNode.GetDisplayNode().SetSelectedColor(1, 0, 0)
                            scoreTextNode.GetDisplayNode().SetActiveColor(1, 0, 0)
                        else:
                            scoreTextNode.GetDisplayNode().SetTextScale(4)
                            scoreTextNode.GetDisplayNode().SetSelectedColor(0, 0, 0)
                            scoreTextNode.GetDisplayNode().SetActiveColor(0, 0, 0)

                        if isGainingScoreStarted:
                            score += tempScore
    totalScore += score
    totalScoreTextNode.SetNthControlPointLabel(0, "$ " + str(round(totalScore)))

    if score > 0:
        scoreTextNode.SetNthControlPointLabel(0, "+" + str(round(score)))
    else:
        scoreTextNode.SetNthControlPointLabel(0, str(round(score)))

    scoreTextNode.SetNthControlPointPosition(0, ras[0], ras[1], ras[2])

    updateVolumeFromArray(userSeesGoldKaleNode, userSeesGoldKaleVolume)


def play():
    global crosshairNode
    crosshairNode = slicer.util.getNode("Crosshair")
    crosshairNodeId = crosshairNode.AddObserver(slicer.vtkMRMLCrosshairNode.CursorPositionModifiedEvent, onMouseMoved)
    global mindedPoints
    mindedPoints = np.zeros(shape=(goldKaleSize[0], goldKaleSize[1], goldKaleSize[2]))
    global isGainingScoreStarted
    isGainingScoreStarted = False
    global totalScore
    totalScore = 0


def calculate_score_for(gtScore, userSeesScore):
    if gtScore == -1 and userSeesScore == -1:
        return -100000

    if gtScore == -1 and userSeesScore == 1:

        return -50000

    elif gtScore == 1 and userSeesScore == -1:

        return 0

    elif gtScore == 1 and userSeesScore == 1:

        return 200
