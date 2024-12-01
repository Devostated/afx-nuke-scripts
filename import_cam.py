import nuke
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
    # Deselect all nodes so the camera doesn't link
    for n in nuke.selectedNodes():
        n["selected"].setValue(False)
    return camera


def readCam(filePath):
    with open(filePath) as file:
        version = 0
        scaleFov = ''
        frame = 0

        last_time = None

        words = ReadLineWords(file)
        if not (len(words) == 2 and 'advancedfx' == words[0] and 'Cam' == words[1]):
            nuke.alert('Not a valid advancedfx Cam file.')
            return False

        # Read metadata
        while True:
            words = ReadLineWords(file)
            if len(words) >= 1 and words[0] == 'DATA':
                break
            if len(words) >= 2:
                if words[0] == 'version':
                    version = int(words[1])
                elif words[0] == 'scaleFov':
                    scaleFov = words[1]

        if version < 1 or version > 2:
            nuke.alert("Invalid version, only 1 - 2 are supported.")
            return False

        if scaleFov not in ['', 'none', 'alienSwarm']:
            nuke.alert("Unsupported scaleFov value.")
            return False

        root = nuke.Root()
        fps = root.fps()
        format = root.format()
        width = format.width()
        height = format.height()

        camera = createCam()

        last_time = None

        # Create temporary knobs
        temp_rotate = nuke.XYZ_Knob("temp_rotate", "Temporary Rotate")
        temp_translate = nuke.XYZ_Knob("temp_translate", "Temporary Translate")
        temp_focal = nuke.Double_Knob("temp_focal", "Temporary Focal")

        temp_rotate.setAnimated()
        temp_translate.setAnimated()
        temp_focal.setAnimated()

        camera['vaperture'].value() == camera['haperture'].value() / width * height

        # Populate temporary knobs
        while True:
            words = ReadLineWords(file)
            if len(words) < 8:
                break

            time = float(words[0])

            if last_time is None:
                last_time = time

            time = time - last_time
            frame = time * fps

            xpos, ypos, zpos = map(float, words[1:4])
            xrot, yrot, zrot = map(float, words[4:7])
            fov = float(words[7])

            # none and alienSwarm was confused in version 1, version 2 always outputs real fov and doesn't have scaleFov.
            if 'none' == scaleFov:
                fov = AlienSwarm_FovScaling(width, height, fov)

            lens = camera['haperture'].value() / (2.0 * math.tan(math.radians(fov) / 2.0))

            rotKeys_y = [(frame, -yrot)]
            rotKeys_z = [(frame, zrot)]
            rotKeys_x = [(frame, -xrot)]

            xrotSmoothed = smoothEulerRotationKeys(rotKeys_y)
            yrotSmoothed = smoothEulerRotationKeys(rotKeys_z)
            zrotSmoothed = smoothEulerRotationKeys(rotKeys_x)

            temp_rotate.setValueAt(xrotSmoothed[0][1], frame, 0)
            temp_rotate.setValueAt(yrotSmoothed[0][1], frame, 1)
            temp_rotate.setValueAt(zrotSmoothed[0][1], frame, 2)

            temp_translate.setValueAt(-ypos * 0.0254, frame, 0)
            temp_translate.setValueAt(zpos * 0.0254, frame, 1)
            temp_translate.setValueAt(-xpos * 0.0254, frame, 2)

            temp_focal.setValueAt(lens, frame, 0)

        # Transfer animations to real knobs
        camera["rotate"].fromScript(temp_rotate.toScript())
        camera["translate"].fromScript(temp_translate.toScript())
        camera["focal"].fromScript(temp_focal.toScript())

    root['last_frame'].setValue(frame)
    nuke.tprint("Imported Camio camera from: " + filePath)

    return True

def importCamio():
    p = nuke.Panel('Import CamIO (.cam)')
    p.addFilenameSearch('Select CamIO File:', '')
    p.addButton('Cancel')
    p.addButton('OK')

    if p.show():
        filePath = p.value('Select CamIO File:')
        if not filePath.endswith('.cam'):
            nuke.alert("Please select a file with a '.cam' extension")
            return False
        else:
            readCam(filePath)
