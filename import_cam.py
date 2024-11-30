import nuke_internal as nuke
import math


def smoothEulerRotationKeys(rotKeys):
    smoothedKeys = []
    prevValue = None

    for frame, value in rotKeys:
        if prevValue is not None:
            diff = value - prevValue
            value += -360 if diff > 180 else 360 if diff < -180 else 0

        smoothedKeys.append((frame, value))
        prevValue = value

    return smoothedKeys


def ReadLineWords(file):
    line = file.readline()
    words = [ll for ll in line.split() if ll]
    return words


def AlienSwarm_FovScaling(width, height, fov):
    if 0 == height:
        return fov
    engineAspectRatio = width / height
    defaultAscpectRatio = 4.0 / 3.0
    ratio = engineAspectRatio / defaultAscpectRatio
    t = ratio * math.tan(math.radians(0.5 * fov))
    return 2.0 * math.degrees(math.atan(t))


def createCam():
    camera = nuke.createNode("Camera3")
    camera['rotate'].setAnimated()
    camera['translate'].setAnimated()
    camera['focal'].setAnimated()
    # get selected nodes
    selected_nodes = nuke.selectedNodes()

    # deselect all nodes so the camera doesn't link
    for n in selected_nodes:
        n["selected"].setValue(False)

    return camera


def readCam(filePath):
    file = open(filePath)
    words = ReadLineWords(file)

    version = 0
    scaleFov = ''
    frame = 0

    if not (2 <= len(words) and 'advancedfx' == words[0] and 'Cam' == words[1]):
        nuke.alert('Not an valid advancedfx Cam file.')
        return False

    while True:
        words = ReadLineWords(file)
        if (1 <= len(words)):
            if 'DATA' == words[0]:
                break
            if 'version' == words[0] and 2 <= len(words):
                version = int(words[1])
            if 'scaleFov' == words[0] and 2 <= len(words):
                scaleFov = words[1]

    if (version < 1 or version > 2):
        nuke.alert("Invalid version, only 1 - 2 are supported.")
        return False

    if not (scaleFov in ['', 'none', 'alienSwarm']):
        nuke.alert("Unsupported scaleFov value.")
        return False

    root = nuke.Root()
    fps = root.fps()
    format = root.format()
    width = format.width()
    height = format.height()

    camera = createCam()

    last_time = None

    # Get animation curves for each axis
    xPosCurve = camera['translate'].animation(0)
    yPosCurve = camera['translate'].animation(1)
    zPosCurve = camera['translate'].animation(2)

    xRotCurve = camera['rotate'].animation(0)
    yRotCurve = camera['rotate'].animation(1)
    zRotCurve = camera['rotate'].animation(2)

    fovCurve = camera['focal'].animation(0)
    camera['vaperture'].value() == camera['haperture'].value() / width * height

    # Prepare lists to collect keys for batch addition
    xKeys, yKeys, zKeys = [], [], []
    xRotKeys, yRotKeys, zRotKeys = [], [], []
    fovKeys = []

    while True:
        words = ReadLineWords(file)
        if not (8 <= len(words)):
            break

        time = float(words[0])

        if last_time is None:
            last_time = time

        time = time - last_time
        frame = time * fps

        xPos = float(words[1])
        yPos = float(words[2])
        zPos = float(words[3])

        xRot = float(words[4])
        yRot = float(words[5])
        zRot = float(words[6])

        fov = float(words[7])

        # none and alienSwarm was confused in version 1, version 2 always outputs real fov and doesn't have scaleFov.
        if 'none' == scaleFov:
            fov = AlienSwarm_FovScaling(width, height, fov)

        lens = camera['haperture'].value(
        ) / (2.0 * math.tan(math.radians(fov) / 2.0))

        # Collect keyframe data and convert units to meters
        xKeys.append((frame, -yPos * 0.0254))
        yKeys.append((frame, zPos * 0.0254))
        zKeys.append((frame, -xPos * 0.0254))

        xRotKeys.append((frame, -yRot))
        yRotKeys.append((frame, zRot))
        zRotKeys.append((frame, -xRot))

        fovKeys.append((frame, lens))

    xRotKeys = smoothEulerRotationKeys(xRotKeys)
    yRotKeys = smoothEulerRotationKeys(yRotKeys)
    zRotKeys = smoothEulerRotationKeys(zRotKeys)

    for frame, value in xKeys:
        xPosCurve.setKey(frame, value)

    for frame, value in yKeys:
        yPosCurve.setKey(frame, value)

    for frame, value in zKeys:
        zPosCurve.setKey(frame, value)

    for frame, value in xRotKeys:
        xRotCurve.setKey(frame, value)

    for frame, value in yRotKeys:
        yRotCurve.setKey(frame, value)

    for frame, value in zRotKeys:
        zRotCurve.setKey(frame, value)

    for frame, value in fovKeys:
        fovCurve.setKey(frame, value)

    root['last_frame'].setValue(frame)
    nuke.tprint("Imported Camio camera from: " + filePath)


def importCamio():
    p = nuke.Panel('Import CamIO (.cam)')
    p.addFilenameSearch('Select CamIO File:', '')
    p.addButton('Cancel')
    p.addButton('OK')

    ret = p.show()

    filePath = p.value('Select CamIO File:')
    if ret:
        if not filePath.endswith('.cam'):
            nuke.alert("Please select a file with a '.cam' extension")
            return False
        else:
            readCam(filePath)
