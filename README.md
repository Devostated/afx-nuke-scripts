# afx-nuke-scripts
Nuke scripts for the advancedfx.org project
## Features
| File Type | Contents                          | Import             | Export            |
| ------    | ------                            | ------             | ------            |
| .CAM      | HLAE Camera IO                    | :heavy_check_mark: | :x:               |
| .BVH      | HLAE Camera Motion Data           | :x:                | Not Planned       |
| .AGR      | Advancedfx Game Recording         | Not Planned        | Not Planned       |
## Download
Downloads are on the [releases page](https://github.com/Devostated/afx-nuke-scripts/releases).
## Instructions
1. Copy import_cam.py into your nuke environment (defaults to C:\Users\%USERNAME%\.nuke)

2. Insert following lines into your menu.py or use the premade one
	
```py
import import_cam
nuke.menu('Nuke').addCommand("Advancedfx/Import CamIO (.cam)", "import_cam.importCamio()")
```
