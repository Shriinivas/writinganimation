![Demo](https://github.com/Shriinivas/etc/blob/master/writinganimation/illustrations/demo.gif)
This add-on generates writing animations for selected Bezier curves or text in Blender.

**Supported Blender Versions:** 2.8x and later

## Installation

This add-on comes integrated with stroke font text animation.

1. Click on the **Code** button above the repository list.
2. Download the zip file to a local folder.
3. Open Blender and navigate to **Edit -> Preferences**.
4. In the Preferences window, go to the **Add-ons** tab and click **Install Add-on from File**.
5. Select the downloaded zip file.
6. Enable the 'Create Writing Animation' option in the add-ons dialog.

After installation, a new 'Writing Animation' tab will appear in object mode under 'Active Tool and Workspace settings' on the properties panel.

## Quick Start

1. Select the Bezier curves.
2. Enter the starting frame and length of the animation.
3. Click 'Create Writing Animation'.
4. Selecting 'Text' in the 'Animate' drop-down, text-specific options will appear. Enter the text you want to animate in the text input box and adjust other option values to create a text writing animation.

For a detailed overview of the add-on functionality and various options, watch [this introductory video](https://youtu.be/_tATQJhAkIg). For a detailed usage example, see [this video tutorial](https://youtu.be/s2BIh-jV8XE).

For more details specifically on automated text writing animation, please refer to [this video](https://youtu.be/WZVMPuyfYTM).

## Limitations

- **Undo Behavior:** If you undo the generate animation operation, the selections made previously with the eye dropper in 'Properties of' and 'Custom Writer' may not function consistently. After undoing, you will need to reselect the corresponding objects, even if they were selected before undoing.
- **Modifiers on Curves:** For curves with modifiers, sometimes the writer and curve are not in sync due to errors in length calculation (root cause still unknown). A workaround is to either:
  - Apply the modifiers on the curve
  - Split the curves into a number of smaller segments (refer to the usage example above) before generating the animation.

For splitting splines, using the [Bezier Utilities](https://github.com/Shriinivas/blenderbezierutils) add-on is recommended as it is more up-to-date.

## License

[GPL 3.0](./LICENSE)
