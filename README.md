![Demo](https://github.com/Shriinivas/etc/blob/master/writinganimation/illustrations/demo.gif)
# Blender Add-on for Generating Writing Animation<br>
This add-on generates writing animation for the selected Bezier curves in blender <br><br>
Supported Blender versions: <b>2.8x</b> and <b>2.79b</b> <br>

# Installation
<b>To install on 2.8x Blender (this comes integrated with stroke font text animation):<br></b>
- Click on the Code button above the repository list
- Download the zip file in a local folder
- Follow the common steps below

<b>To install on 2.79b (this is without stroke font text animation):<br></b>
- Click on the writinganim.py link
- Click on the Raw button above the code listing
- Press control+s to save the file in a local folder
- Follow the common steps below

<b>Common Steps:</b>
- Open Blender and select Edit (or File in 2.79b)->User Preferences <br>
- Click install Add-ons tab and then Install Add-on from File<br>
- Select the downloaded file <br>
- Check the 'Create Writing Animation' option in the add-ons dialog <br>

After installation, a new 'Writing Animation' tab is displayed in object mode. In Blender 2.79 it's on the tools panel, in 2.8  it's on 'Active Tool and Workspace settings' tab on the properties panel.

# Quick start
Select the bezier curves, enter startig frame and length of the animation and click 'Create Writing Animation'<br>

<a href=https://youtu.be/_tATQJhAkIg> The introductory video</a> provides a detailed overview of the add-on functionality and various options available. Additionally <a href=https://youtu.be/s2BIh-jV8XE>this video tutorial</a> covers a detailed usage example.

If you have installed the integrated zip (available only for Blender 2.8), there will be an additional option 'Animate' at the top. Selecting 'Text' in this drop down will display text specific options below. You can enter the text to be animated in the text input box and taylor other option values to create a text writing animation.

Please refer to <a href=https://youtu.be/WZVMPuyfYTM> this video </a> for more details on the automated text writing  animation.

# Limitations
If you undo the generate animation operation, the eye dropper selections made previously in 'Properties of' and 'Custom Writer'  options do not function consistently. So after undoing, even if these options show some values, you will have to select the corresponding objects once again (if they were selected before undoing).<br><br>
For curves with modifiers, sometimes the writer and curve are not in sync due to some error in length calculation (root cause still unknown). A workaround for this is to either (a) apply the modifiers on the curve or (b) split the curves into a number of smaller segments (refer to the usage example above) before generating the animation.

Exercise caution when using this add-on in production as it's in alpha stage<br>

# License
<a href=https://github.com/Shriinivas/writinganimation/blob/master/LICENSE>MIT</a>
