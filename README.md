# Prerequisites
Install Python 3.7 https://www.python.org/downloads/  
Run "pip install pillow"  
Download ndstool.exe and place it inside this folder https://www.darkfader.net/ds/files/ndstool.exe  
Download NerdFontTerminatoR.exe and place it inside this folder https://github.com/pleonex/NerdFontTerminatoR/releases  
# Extraction
Copy the rom as "rom.nds" inside this folder  
Run "extract_rom.py" to extract the ROM in the "extract" folder with ndstool  
Run "extract_nfp.py" to extract the NFP files in the "extract_NFP" and "work_NFP" folder  
Run "extract_spc.py" to extract the SPC lines in the "spc_input.txt" file  
Run "extract_bin.py" to extract the BIN lines in the "bin_input.txt" file  
Run "extract_3dg.py" to extract the 3DG textures in the "work_3DG" folder and a "3dg_data.txt" file used by the repacker  
Run "extract_yce.py" to extract the YCE images in the "work_YCE" folder and a "yce_data.txt" file used by the repacker  
Run "extract_kpc.py" to extract the KPC images in the "work_KPC" folder  
# Font Editing
Edit "font.png", the needed bigrams will be automatically generated by the repacker  
More symbols can be added by editing the top of the "repack_font.py" file  
# Text Editing
Edit the "spc_input.txt" and "bin_input.txt" files  
Control codes are written as &lt;XX&gt; and they should be kept. &lt;0A&gt; is a line break, the other are currently unknown  
The bin_input file contains more codes in the format of UNK(XXXX), these should always be kept  
A "|" can be used to make a single-line message become a two-lines message  
If the translated line starts with "<<", the line will be padded with spaces at the beginning and end up to 20 characters, for buttons with centered kanji  
">>" can be used to add a new dialogue box after the current line. Example: "しっかり掘れ～～！=Keep digging!>>Testing>>More than one"  
Comments can be added at the end of the lines by using #  
# Image Editing
Edit the images in the "work_3DG", "work_KPC" and "work_YCE" folders. The palette on the right should be followed but the repacker will try to approximate other colors to the nearest one  
If an image doesn't require repacking, it should be deleted from the work folder  
# Repacking
Run "repack.py" to generate "rom_patched.nds"  
If you only want to repack NFP and patch the rom, you can use "repack.py -nfp"  
You can also use the following parameters to only repack specific types: -spc, -bin, -3dg, -kpc, -yce  
For example "repack.py -spc -bin" will only repack SPC, BIN, NFP and patch the rom  
The "-deb" parameter is also available and when used it will send the player to the Debug Map when starting a new game  
