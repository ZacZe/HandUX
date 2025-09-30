# Hi. Welcome to HandUX, a hand-tracking tool. 

<mark> !!! THIS IS A WORK IN PROGRESS, I WILL DIVIDE THE PROGRAM INTO INDIVIDUAL MODULES FOR EASY VIEWING !!! </mark>

## Requirements: 
You must have the following installed: 
- mediapipe (Python)
- OpenCV-Python (Python)
- PYAutoGUI (Python)
- numpy (Python)

## How to Use: 
The cursor is controlled by the movement of the tip of the index finger. 

In order to left click, tap the tip of your thumb with the tip of your index finger. Holding requires touching said tips for a duration of time. 

In order to right click, tap the tip of your thumb with the tip of your middle finger. 

There are plans for there to be settings where you can change the fingers used to do these actions. 

Pressing <code>SPACEBAR</code> will pause or resume the webcam footage. This can be used to temporarily disable this program. 

Pressing <code>ESCAPE</code> will close the program. 

## Extra Features: 
Pressing <code>s</code> will toggle the skeleton of the active hand. This can be used to see how this program registers actions. 

Pressing <code>t</code> will toggle gesture text for improved user experience. This can be used to detect if the gestures are being understood. 

Pressing <code>x</code> will toggle the variable settings. You can adjust the sensitivity and holding time threshold of your gestures.

Pressing <code>n</code> will toggle dual-hand mode. The right hand controls the cursor, whilst the left hand controls the actions. 

## Future Features: 
These features are currently a work-in-progress and should be implemented soon. 
- Multi-hand tracking for specific or custom actions
- Custom behaviours from specific gestures
- Specific modes for specific activities, eg: drawing or gaming
- Settings to customise fingers used in gestures
