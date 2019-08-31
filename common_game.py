import codecs
import os
import struct
from PIL import Image, ImageOps
import common

# Control codes found in strings
codes = [0x09, 0x0A, 0x20, 0xA5]
# Control codes and random ASCII characters found in BIN strings
bincodes = [0x09, 0x0A, 0x20, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x42, 0x43, 0x64, 0xA5]
# Identifier and size of SPC code blocks
spccodes = {
    0x28: 1, 0x2A: 1, 0x54: 1, 0x58: 1, 0x59: 1, 0x5A: 1, 0x5B: 1, 0x5C: 1, 0x5D: 1, 0x8F: 1,
    0x20: 2, 0x50: 2, 0x52: 2, 0x72: 2, 0x73: 2, 0x79: 2,
    0x11: 4, 0x29: 4, 0x80: 4, 0x81: 4, 0x3A: 4,
    0x12: 5, 0x21: 5, 0x31: 5, 0x33: 5, 0x37: 5, 0x39: 5
}
# Font table
table = {}


# Game-specific strings
def readShiftJIS(f):
    len = f.readShort()
    pos = f.tell()
    # Check if the string is all ascii
    ascii = True
    for i in range(len - 1):
        byte = f.readByte()
        if byte != 0x0A and (byte < 32 or byte > 122):
            ascii = False
            break
    if not ascii:
        f.seek(pos)
        sjis = ""
        i = 0
        while i < len - 1:
            byte = f.readByte()
            if byte in codes:
                sjis += "<" + common.toHex(byte) + ">"
                i += 1
            else:
                f.seek(-1, 1)
                try:
                    sjis += f.read(2).decode("shift-jis").replace("〜", "～")
                except UnicodeDecodeError:
                    print("[ERROR] UnicodeDecodeError")
                    sjis += "|"
                i += 2
        return sjis
    return ""


def writeShiftJIS(f, str, writelen=True, maxlen=0):
    if str == "":
        if writelen:
            f.writeShort(1)
        f.writeByte(0)
        return 1
    i = 0
    strlen = 0
    if writelen:
        lenpos = f.tell()
        f.writeShort(strlen)
    if ord(str[0]) < 256 or str[0] == "“" or str[0] == "”" or str[0] == "↓":
        # ASCII string
        while i < len(str):
            # Add a space if the next character is <XX>, UNK(XXXX) or CUS(XXXX)
            if i < len(str) - 1 and str[i+1] == "<":
                str = str[:i+1] + " " + str[i+1:]
            elif i < len(str) - 4 and (str[i+1:i+5] == "UNK(" or str[i+1:i+5] == "CUS("):
                str = str[:i+1] + " " + str[i+1:]
            char = str[i]
            # Code format <XX>
            if char == "<" and i < len(str) - 3 and str[i+3] == ">":
                try:
                    code = str[i+1] + str[i+2]
                    f.write(bytes.fromhex(code))
                    strlen += 1
                except ValueError:
                    print("[ERROR] Invalid escape code", str[i+1], str[i+2])
                i += 4
            # Unknown format UNK(XXXX)
            elif char == "U" and i < len(str) - 4 and str[i:i+4] == "UNK(":
                code = str[i+4] + str[i+5]
                f.write(bytes.fromhex(code))
                code = str[i+6] + str[i+7]
                f.write(bytes.fromhex(code))
                i += 9
                strlen += 2
                if maxlen > 0 and strlen >= maxlen:
                    return -1
            # Custom full-size glyph CUS(XXXX)
            elif char == "C" and i < len(str) - 4 and str[i:i+4] == "CUS(":
                f.write(bytes.fromhex(table[str[i+4:i+8]]))
                i += 9
                strlen += 2
                if maxlen > 0 and strlen >= maxlen:
                    return -1
            else:
                if i + 1 == len(str):
                    bigram = char + " "
                else:
                    bigram = char + str[i+1]
                i += 2
                if bigram not in table:
                    if common.warning:
                        try:
                            print(" [WARNING] Bigram not found:", bigram, "in string", str)
                        except UnicodeEncodeError:
                            print(" [WARNING] Bigram not found in string", str)
                    bigram = "  "
                f.write(bytes.fromhex(table[bigram]))
                strlen += 2
                if maxlen > 0 and strlen >= maxlen:
                    return -1
    else:
        # SJIS string
        str = str.replace("～", "〜")
        while i < len(str):
            char = str[i]
            if char == "<":
                code = str[i+1] + str[i+2]
                i += 4
                f.write(bytes.fromhex(code))
                strlen += 1
            else:
                i += 1
                f.write(char.encode("shift-jis"))
                strlen += 2
    if writelen:
        f.writeZero(1)
        pos = f.tell()
        f.seek(lenpos)
        f.writeShort(strlen + 1)
        f.seek(pos)
    return strlen + 1


def detectShiftJIS(f):
    ret = ""
    while True:
        b1 = f.readByte()
        if ret != "" and b1 == 0:
            return ret
        if ret != "" and b1 in bincodes:
            ret += "<" + common.toHex(b1) + ">"
            continue
        b2 = f.readByte()
        if common.checkShiftJIS(b1, b2):
            f.seek(-2, 1)
            try:
                ret += f.read(2).decode("cp932").replace("〜", "～")
            except UnicodeDecodeError:
                if ret.count("UNK(") >= 5:
                    return ""
                ret += "UNK(" + common.toHex(b1) + common.toHex(b2) + ")"
        elif len(ret) > 0 and ret.count("UNK(") < 5:
            ret += "UNK(" + common.toHex(b1) + common.toHex(b2) + ")"
        else:
            return ""


def loadTable():
    if os.path.isfile("data/table.txt"):
        with codecs.open("data/table.txt", "r", "utf-8") as ft:
            for line in ft:
                line = line.strip("\r\n")
                if line.find("=") > 0:
                    linesplit = line.split("=", 1)
                    table[linesplit[0]] = linesplit[1]


# Game-specific textures
class YCETexture:
    width = 0
    height = 0
    offset = 0
    size = 0
    oamnum = 0
    oamsize = 0
    tilesize = 0
    paloffset = 0
    oams = []


class OAM:
    x = 0
    y = 0
    width = 0
    height = 0
    offset = 0


def readPaletteData(paldata):
    palettes = []
    for j in range(len(paldata) // 32):
        palette = []
        for i in range(0, 32, 2):
            p = struct.unpack("<H", paldata[j * 32 + i:j * 32 + i + 2])[0]
            palette.append(common.readPalette(p))
        palettes.append(palette)
    if common.debug:
        print(" Loaded", len(palettes), "palettes")
    return palettes


def readMappedImage(imgfile, width, height, paldata, fixtrasp=False, tilesize=8):
    palettes = readPaletteData(paldata)
    # Read the image
    img = Image.open(imgfile)
    img = img.convert("RGBA")
    pixels = img.load()
    # Split image into tiles and maps
    tiles = []
    maps = []
    i = j = 0
    while i < height:
        tilecolors = []
        for i2 in range(tilesize):
            for j2 in range(tilesize):
                tilecolors.append(pixels[j + j2, i + i2])
        pal = common.findBestPalette(palettes, tilecolors)
        tile = []
        for tilecolor in tilecolors:
            tile.append(common.getPaletteIndex(palettes[pal], tilecolor, fixtrasp))
        # Search for a repeated tile
        found = -1
        for ti in range(len(tiles)):
            if tiles[ti] == tile:
                found = ti
                break
        if found != -1:
            maps.append((pal, 0, 0, found))
        else:
            tiles.append(tile)
            maps.append((pal, 0, 0, len(tiles) - 1))
        j += tilesize
        if j >= width:
            j = 0
            i += tilesize
    return tiles, maps


def drawMappedImage(width, height, mapdata, tiledata, paldata, tilesize=8, bpp=4):
    palnum = len(paldata) // 32
    img = Image.new("RGBA", (width + 40, max(height, palnum * 10)), (0, 0, 0, 0))
    pixels = img.load()
    # Maps
    maps = []
    for i in range(0, len(mapdata), 2):
        map = struct.unpack("<h", mapdata[i:i+2])[0]
        pal = (map >> 12) & 0xF
        xflip = (map >> 10) & 1
        yflip = (map >> 11) & 1
        tile = map & 0x3FF
        maps.append((pal, xflip, yflip, tile))
    if common.debug:
        print(" Loaded", len(maps), "maps")
    # Tiles
    tiles = []
    for i in range(len(tiledata) // (32 if bpp == 4 else 64)):
        singletile = []
        for j in range(tilesize * tilesize):
            x = i * (tilesize * tilesize) + j
            if bpp == 4:
                index = (tiledata[x // 2] >> ((x % 2) << 2)) & 0x0f
            else:
                index = tiledata[x]
            singletile.append(index)
        tiles.append(singletile)
    if common.debug:
        print(" Loaded", len(tiles), "tiles")
    # Palette
    palettes = readPaletteData(paldata)
    pals = []
    for palette in palettes:
        pals += palette
    # Draw the image
    i = j = 0
    for map in maps:
        try:
            pal = map[0]
            xflip = map[1]
            yflip = map[2]
            tile = tiles[map[3]]
            for i2 in range(tilesize):
                for j2 in range(tilesize):
                    pixels[j + j2, i + i2] = pals[16 * pal + tile[i2 * tilesize + j2]]
            # Very inefficient way to flip pixels
            if xflip or yflip:
                sub = img.crop(box=(j, i, j + tilesize, i + tilesize))
                if yflip:
                    sub = ImageOps.flip(sub)
                if xflip:
                    sub = ImageOps.mirror(sub)
                img.paste(sub, box=(j, i))
        except (KeyError, IndexError):
            print("  [ERROR] Tile", map[3], "not found")
        j += tilesize
        if j >= width:
            j = 0
            i += tilesize
    # Draw palette
    if len(palettes) > 0:
        for i in range(len(palettes)):
            pixels = common.drawPalette(pixels, palettes[i], width, i * 10)
    return img