import struct
import os
import math

debug = False
warning = False
codes = [0x0A, 0x09, 0xA5, 0x20]
bincodes = [0x0A, 0x09, 0xA5, 0x20, 0x42, 0x43, 0x32, 0x64]
table = {}


def toHex(byte):
    hexstr = hex(byte)[2:].upper()
    if len(hexstr) == 1:
        return "0" + hexstr
    return hexstr


def readInt(f):
    return struct.unpack("<i", f.read(4))[0]


def readUInt(f):
    return struct.unpack("<I", f.read(4))[0]


def readShort(f):
    return struct.unpack("<h", f.read(2))[0]


def readUShort(f):
    return struct.unpack("<H", f.read(2))[0]


def readByte(f):
    return struct.unpack("B", f.read(1))[0]


def readPalette(f):
    p = readShort(f)
    return (((p >> 0) & 0x1f) << 3, ((p >> 5) & 0x1f) << 3, ((p >> 10) & 0x1f) << 3, 0xff)


def readString(f, length):
    str = ""
    for i in range(length):
        byte = readByte(f)
        # These control characters can be found in texture names, replace them with a space
        if byte == 0x82 or byte == 0x86:
            byte = 0x20
        if byte != 0:
            str += chr(byte)
    return str


def readShiftJIS(f):
    len = readShort(f)
    pos = f.tell()
    # Check if the string is all ascii
    ascii = True
    for i in range(len - 1):
        byte = readByte(f)
        if byte != 0x0A and (byte < 32 or byte > 122):
            ascii = False
            break
    if not ascii:
        f.seek(pos)
        sjis = ""
        i = 0
        while i < len - 1:
            byte = readByte(f)
            if byte in codes:
                sjis += "<" + toHex(byte) + ">"
                i += 1
            else:
                f.seek(-1, 1)
                sjis += f.read(2).decode("shift-jis").replace("〜", "～")
                i += 2
        return sjis
    return ""


def writeInt(f, num):
    f.write(struct.pack("<i", num))


def writeShort(f, num):
    f.write(struct.pack("<h", num))


def writeByte(f, num):
    f.write(struct.pack("B", num))


def writeString(f, str):
    f.write(str.encode("ascii"))


def writeZero(f, num):
    for i in range(num):
        writeByte(f, 0)


def writeShiftJIS(f, str, writelen=True):
    if str == "":
        if writelen:
            writeShort(f, 1)
        writeByte(f, 0)
        return 1
    i = 0
    strlen = 0
    if writelen:
        lenpos = f.tell()
        writeShort(f, strlen)
    if ord(str[0]) < 256:
        # ASCII string
        while i < len(str):
            if i < len(str) - 1 and (str[i+1] == "<"):
                str = str[:i+1] + " " + str[i+1:]
            char = str[i]
            if char == "<":
                code = str[i+1] + str[i+2]
                i += 4
                f.write(bytes.fromhex(code))
                strlen += 1
            else:
                if i+1 == len(str):
                    bigram = char + " "
                else:
                    bigram = char + str[i+1]
                bigram = bigram.replace("’", "'").replace("“", "\"").replace("”", "\"")
                i += 2
                if bigram not in table:
                    if warning:
                        print(" [WARNING] Bigram not found: " + bigram)
                    bigram = "  "
                f.write(bytes.fromhex(table[bigram]))
                strlen += 2
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
        writeZero(f, 1)
        pos = f.tell()
        f.seek(lenpos)
        writeShort(f, strlen + 1)
        f.seek(pos)
    return strlen + 1


def writePointer(f, pointer, pointerdiff):
    newpointer = pointer
    for k, v in pointerdiff.items():
        if k < pointer:
            newpointer += v
    if debug:
        print("  Shifted pointer " + str(pointer+16) + " to " + str(newpointer+16))
    writeInt(f, newpointer)


def isStringPointer(f):
    readByte(f)
    b2 = readByte(f)
    b3 = readByte(f)
    b4 = readByte(f)
    # print("Signature: " + hex(b1) + " " + hex(b2) + " " + hex(b3) + " " + hex(b4))
    if (b2 == 0 or b2 == 0x28 or b2 == 0x2A) and b3 == 0 and b4 == 0x10:
        return True
    return False


def getSection(f, title):
    f.seek(0)
    ret = {}
    found = title == ""
    for line in f:
        if not found and line.startswith("!FILE:" + title):
            found = True
        elif found:
            if line.startswith("!FILE:"):
                break
            elif line.find("=") > 0:
                split = line[:-1].split("=", 1)
                split[1] = split[1].split("#")[0]
                ret[split[0]] = split[1]
    return ret


def checkShiftJIS(first, second):
    # Based on https://www.lemoda.net/c/detect-shift-jis/
    status = False
    if (first >= 0x81 and first <= 0x84) or (first >= 0x87 and first <= 0x9f):
        if second >= 0x40 and second <= 0x93:
            status = True
        elif second >= 0x9f and second <= 0xfc:
            status = True
    elif first >= 0xe0 and first <= 0xef:
        if second >= 0x40 and second <= 0x93:
            status = True
        elif second >= 0x9f and second <= 0xfc:
            status = True
    return status


def detectShiftJIS(f):
    ret = ""
    while True:
        b1 = readByte(f)
        if ret != "" and b1 == 0:
            return ret
        if ret != "" and b1 in bincodes:
            ret += "<" + toHex(b1) + ">"
            continue
        b2 = readByte(f)
        if checkShiftJIS(b1, b2):
            f.seek(-2, 1)
            try:
                ret += f.read(2).decode("shift-jis").replace("〜", "～")
            except UnicodeDecodeError:
                return ""
        else:
            return ""


def getColorDistance(c1, c2):
    (r1, g1, b1, a1) = c1
    (r2, g2, b2, a2) = c2
    return math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)


def getPaletteIndex(palette, color):
    if color[3] == 0:
        return 0
    for i in range(1, len(palette)):
        if palette[i][0] == color[0] and palette[i][1] == color[1] and palette[i][2] == color[2]:
            return i
    if palette[0][0] == color[0] and palette[0][1] == color[1] and palette[0][2] == color[2]:
        return 0
    if debug:
        print("  Color " + str(color) + " not found, finding closest color ...")
    mindist = 999999
    disti = 0
    for i in range(1, len(palette)):
        distance = getColorDistance(color, palette[i])
        if distance < mindist:
            mindist = distance
            disti = i
    if debug:
        print("  Closest color: " + str(palette[disti]))
    return disti


def loadTable():
    if os.path.isfile("table.txt"):
        with open("table.txt", "r") as ft:
            for line in ft:
                table[line[:2]] = line[3:7]
