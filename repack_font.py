import codecs
import os
from PIL import Image
import game
from hacktools import common


def run():
    xmlfile = "data/fontdump.xml"
    imgfile = "data/fontdump.png"
    fontfile = "font.png"
    fontconfigfile = "fontconfig.txt"
    outfile = "data/fontout.png"
    infont = "data/extract_NFP/ETC.NFP/GL_12FNT.NFT"
    tempfont = "data/GL_12FNT.NFTR"
    outfont = "data/work_NFP/ETC.NFP/GL_12FNT.NFT"
    binin = "data/bin_input.txt"
    spcin = "data/spc_input.txt"
    table = "data/table.txt"

    common.logMessage("Repacking font ...")
    fontexe = common.bundledFile("NerdFontTerminatoR.exe")
    if not os.path.isfile(fontexe):
        common.logError("NerdFontTerminatoR not found")
        return

    # List of characters
    with codecs.open(fontconfigfile, "r", "utf-8") as f:
        fontconfig = common.getSection(f, "")
        upperchars = fontconfig["upperchars"][0].split("|")
        lowerchars = fontconfig["lowerchars"][0].split("|")
        numbers = fontconfig["numbers"][0].split("|")
        punctuation = fontconfig["punctuation"][0].split("|")
        customs = fontconfig["customs"][0].split("|")
        all = upperchars + lowerchars + numbers + punctuation + customs

    # X Position in the font.png file
    positions = {}
    for i in range(len(upperchars)):
        positions[upperchars[i]] = i * 12
        positions[lowerchars[i]] = (i * 12) + 6
    for i in range(len(numbers)):
        positions[numbers[i]] = (len(upperchars) * 12) + (i * 6)
    for i in range(len(punctuation)):
        positions[punctuation[i]] = (len(upperchars) * 12) + (len(numbers) * 6) + (i * 6)
    for i in range(len(customs)):
        positions[customs[i]] = (len(upperchars) * 12) + (len(numbers) * 6) + (len(punctuation) * 6) + (i * 12)

    # Fix the font size before dumping it
    with common.Stream(infont, "rb") as font:
        with common.Stream(tempfont, "wb") as temp:
            font.seek(8)
            size = font.readUInt()
            font.seek(0)
            temp.write(font.read(size))
    # Dump the font
    common.execute(fontexe + " -e " + tempfont + " " + xmlfile + " " + imgfile, False)

    # Generate the code range
    coderanges = [(0x89, 0x9F), (0xE0, 0xEA)]
    skipcodes = [0x7F]
    charrange = (0x40, 0xFC)
    codes = []
    for coderange in coderanges:
        for i in range(coderange[0], coderange[1] + 1):
            first = charrange[0]
            if i == 0x88:
                first = 0x9F
            last = charrange[1]
            if i == 0xEA:
                last = 0xA4
            for j in range(first, last + 1):
                if j in skipcodes:
                    continue
                hexcode = i * 0x100 + j
                if hexcode > 0x9872 and hexcode < 0x989F:
                    continue
                codes.append(hexcode)

    # Generate a basic bigrams list
    items = ["  "]
    for char1 in upperchars:
        for char2 in lowerchars:
            items.append(char1 + char2)
    for char1 in upperchars:
        items.append(" " + char1)
        items.append(char1 + " ")
        for char2 in upperchars:
            if char1 + char2 not in items:
                items.append(char1 + char2)
    for char1 in lowerchars:
        items.append(" " + char1)
        items.append(char1 + " ")
        for char2 in lowerchars:
            if char1 + char2 not in items:
                items.append(char1 + char2)
    for custom in customs:
        items.append(custom)
    # And a complete one from all the bigrams
    with codecs.open(spcin, "r", "utf-8") as spc:
        inputs = common.getSection(spc, "", "#", game.fixchars, justone=False)
    with codecs.open(binin, "r", "utf-8") as bin:
        inputs.update(common.getSection(bin, "", "#", game.fixchars, justone=False))
    for k, input in inputs.items():
        for str in input:
            str = "<0A>".join(str.replace("|", "<0A>").split(">>"))
            if str.startswith("<<"):
                str = str[2:]
                pad = " " * ((20 - len(str)) // 2)
                str = pad + str + pad
            if str.startswith("[") and str[3] == "]":
                str = str[4:]
            i = 0
            while i < len(str):
                if i < len(str) - 1 and str[i+1] == "<":
                    str = str[:i+1] + " " + str[i+1:]
                elif i < len(str) - 4 and (str[i+1:i+5] == "UNK(" or str[i+1:i+5] == "CUS("):
                    str = str[:i+1] + " " + str[i+1:]
                char = str[i]
                if char == "<" and i < len(str) - 3 and str[i+3] == ">":
                    i += 4
                elif char == "U" and i < len(str) - 4 and str[i:i+4] == "UNK(":
                    i += 9
                elif char == "C" and i < len(str) - 4 and str[i:i+4] == "CUS(":
                    i += 9
                else:
                    if i + 1 == len(str):
                        bigram = char + " "
                    else:
                        bigram = char + str[i+1]
                    i += 2
                    if bigram not in items:
                        if bigram[0] not in all or bigram[1] not in all:
                            common.logError("Invalid bigram", bigram, "from phrase", str)
                        else:
                            items.append(bigram)

    # Open the images
    img = Image.open(imgfile)
    pixels = img.load()
    font = Image.open(fontfile)
    fontpixels = font.load()

    # Generate the image and table
    fontx = 106
    fonty = 5644
    x = len(codes) - 1
    tablestr = ""
    for item in items:
        if item in customs:
            for i2 in range(11):
                for j2 in range(11):
                    pixels[fontx + i2, fonty + j2] = fontpixels[positions[item] + i2, j2]
        else:
            for i2 in range(5):
                for j2 in range(11):
                    pixels[fontx + i2, fonty + j2] = fontpixels[positions[item[0]] + i2, j2]
            for j2 in range(11):
                pixels[fontx + 5, fonty + j2] = fontpixels[positions[" "], j2]
            for i2 in range(5):
                for j2 in range(11):
                    pixels[fontx + i2 + 6, fonty + j2] = fontpixels[positions[item[1]] + i2, j2]
        fontx -= 13
        if fontx < 0:
            fontx = 197
            fonty -= 13
        tablestr = (item + "=" + common.toHex(codes[x], True) + "\n") + tablestr
        x -= 1
    with codecs.open(table, "w", "utf-8") as f:
        f.write(tablestr)
    img.save(outfile, "PNG")

    # Generate the new font
    common.execute(fontexe + " -i " + xmlfile + " " + outfile + " " + tempfont, False)
    common.copyFile(tempfont, outfont)
    # Clean up the temp files
    os.remove(xmlfile)
    os.remove(imgfile)
    os.remove(outfile)
    os.remove(tempfont)

    if x < len(items):
        common.logMessage("Done! Couldn't fit", len(items) - x, "bigrams")
    else:
        common.logMessage("Done! Room for", x - len(items), "more bigrams")
