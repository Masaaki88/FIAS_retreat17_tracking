# Videotheremin
virtual musical instrument

## What is this?
The videotheremin is a virtual musical instrument which requires just a computer and a webcam. Its inspired by the theremin, an electronic musical instrument controlled without physical contact by the thereminist (performer) [more info see e.g. https://en.wikipedia.org/wiki/Theremin]. The theremin consists of two antennas, one to control the pitch and the other to control the volume. In contrast, the videotheremin uses a webcam to detect the position of the hands.

## Requirements
- a webcam and speakers/headphones
- python with numpy, scipy, matplotlib
- python-opencv

## Usage
Start the videotheremin by executing ./videotheremin.py
Two windows named 'videotheremin' and 'calibration' will pop up. In the 'videotheremin' window you can click on the objects which you want to use to control the sound. The detection algorithm will search for these colors to locate the objects, therefore it works best if the colors of the objects is distinct from all colors in the background. In the 'calibration' window you can adjust the threshold for hue, saturation and value. In the optimal case this window shows the chosen object as white while everything else is black. After the calibration click again in the 'videotheremin' window to start playing.

Keyboard commands:
* Press 'ESC' to quit.
* Press '1' to '9' to choose a timbre. (to define new timbres search for 'spectra' in videotheremin.py) 
* Press 'up'/'down' to adjust the echo.
* Press 'o' to toggle the overlay.
* Press 'c' to redo the calibration, e.g. if you want to replace the objects or if the ilumination changed.

## Troubleshooting
### When moving fast, the pitch does not follow smoothly but jump from one position to another 
If the frame rate is low small objects which are moved fast may blur which makes it hard to detect the position. You can see this effect in the 'calibration' window.  Either choose a bigger object to compensate the effect, or try to get a higher frame rate. To see the current frame rate check the output after the calibration. One likely reason for a small frame rate (e.g. below 20) is that it is just too dark and the webcam increased the exposure to compensate. 

## Ideas for improovements:
* The current reverb effect is a simple feedback loop which produces some annoying inteferences. It would be nice to implement something more sophisticated, e.g. Schroeder's Reverberator (idea: https://christianfloisand.wordpress.com/2012/09/04/digital-reverberation/ , example implementation: https://sites.google.com/site/ldpyproject/under-the-cover/dependencies-py )
* Add a polyphone mode. 
* Split the screen vertically in different registers.
* In the beginning there is some noise which usually vanishes after a few seconds. Any idea why this happens?

## Credits
The soundio module is a modification of the soundio submodule in scikits-audiolab (https://cournape.github.io/audiolab/).

