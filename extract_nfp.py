import os
import shutil
import common

infolder = "extract/data/"
outfolder = "extract_NFP/"
if os.path.isdir(outfolder):
    shutil.rmtree(outfolder)
os.mkdir(outfolder)
workfolder = "work_NFP/"
if os.path.isdir(workfolder):
    shutil.rmtree(workfolder)

for file in os.listdir(infolder):
    print("Processing " + file + " ...")
    os.mkdir(outfolder + file)
    with open(infolder + file, "rb") as f:
        f.seek(52) # Header: NFP2.0 (c)NOBORI 1997-2006
        filenum = common.readInt(f)
        f.seek(4, 1) # Always 0x50
        datastart = common.readInt(f)
        f.seek(16, 1) # All 0
        print(" Found " + str(filenum) + " files, data starting at " + str(datastart))
        for i in range(filenum):
            # Filenames are always 16 bytes long, padded with 0s
            subname = ""
            for j in range(16):
                byte = common.readByte(f)
                if byte != 0:
                    subname += chr(byte)
            # Read starting position and size (multiplied by 4)
            startpos = common.readInt(f)
            size = int(common.readInt(f) / 4)
            # Extract the file
            if common.debug:
                print(" Extracting " + subname + " starting at " + str(startpos) + " with size " + str(size))
            savepos = f.tell()
            f.seek(startpos)
            with open(outfolder + file + "/" + subname, "wb") as newf:
                newf.write(f.read(size))
            f.seek(savepos)

# Copy everything to the work folder
shutil.copytree(outfolder, workfolder)