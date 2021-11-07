Finger-Tapping Random Sequence Generation Task
=========

## Installation of Dependencies

On Mac: 
`pip install -r requirements.txt` or `pip3 install -r requirements.txt`

## To make sure TMS pulses are delivered

1. Before plugging in Master-8 in a USB port, retrieve the list of addresses of all the devices associated with the Mac: `ls /dev`
2. Plug in Master-8.
3. Call the same command as in 1. to see whether a new address has been added to the list. The address you are looking for is of type `dev/cu.usbserial-xxxxxx`. Pass this address as an argument in line 17 of `rTMS_ftrsgt.py` like so: `TMS = m.Master8('/dev/cu.usbserial-xxxxxx')`
4. Before starting `rTMS_ftrsgt_vs.py`, make sure the TMS device is ready.

## Retrieve Script

1. Open Terminal.
2. Go to the directory where you want to place this repository, like so: `cd path` where `path` is the path to the desired directory. Press Enter.
3. Verify that you are operating in the intended directory by typing `ls` and pressing Enter. Terminal will retrieve the content of the said directory.
4. Clone this repository to the directory like so: `git clone https://github.com/victoris93/mind-wandering-finger-tapping.git`
5. Go the to the cloned repository like so: `cd mind-wandering-finger-tapping`.
6. To launch the task script, type `python ftrsgt_vs.py` (with TMS: `python rTMS_ftrsgt_vs.py`) and press Enter.