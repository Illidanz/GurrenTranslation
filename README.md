# Ookami Translation
## Setup
Create a "data" folder and copy the rom as "rom.nds" in it.  
## Run from binary
Download the latest [release](https://github.com/Illidanz/GurrenTranslation/releases) outside the data folder.  
Run "tool extract" to extract everything and "tool repack" to repack after editing.  
Run "tool extract --help" or "tool repack --help" for more info.  
The "--deb" parameter for repacking will send the player to the Debug Map when starting a new game.  
## Run from source
Install [Python 3.7](https://www.python.org/downloads/), pip and virtualenv.  
Download [ndstool.exe](https://www.darkfader.net/ds/files/ndstool.exe).  
Download [NerdFontTerminatoR.exe](https://github.com/pleonex/NerdFontTerminatoR/releases).  
Download xdelta.exe.  
Pull [hacktools](https://github.com/Illidanz/hacktools) in the parent folder.  
```
virtualenv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -e ../hacktools
```
Run tool.py or build with build.bat  
## Font Editing
Edit "font.png", the needed bigrams will be automatically generated by the repacker.  
More symbols can be added by editing the "fontconfig.txt" file.  
Custom full-glyphs can also be added, and then used with the syntax CUS(NAME) in strings. NAME must be 4 characters long.  
## Text Editing
Rename the \*\_output.txt files to \*\_input.txt (bin_output.txt to bin_input.txt, etc) and add translations for each line after the "=" sign.  
New textboxes can be added by appending ">>" followed by the new text.  
Control codes are specified as \<XX\> or UNK(XXXX), they should usually be kept. Line breaks are specified as "<0A>".  
To blank out a line, use a single "!". If just left empty, the line will be left untranslated.  
Comments can be added at the end of lines by using #  
## Image Editing
Rename the out\_\* folders to work\_\* (out_KPC to work_KPC, etc).  
Edit the images in the work folder(s). The palette on the right should be followed but the repacker will try to approximate other colors to the closest one.  
If an image doesn't require repacking, it should be deleted from the work folder.  
