import codecs
import game
from hacktools import common


def run():
    infile = "data/extract/arm9.bin"
    outfile = "data/bin_output.txt"
    # Set to False to analyze the whole file
    limit = True

    common.logMessage("Extracting BIN to", outfile, "...")
    with codecs.open(outfile, "w", "utf-8") as out:
        with common.Stream(infile, "rb") as f:
            # Skip the beginning and end of the file to avoid false-positives
            f.seek(992000 if limit else 900000)
            foundstrings = []
            while f.tell() < 1180000:
                pos = f.tell()
                if not limit or pos < 1010000 or pos > 1107700:
                    check = game.detectShiftJIS(f)
                    # Save the string if we detected one
                    if check != "":
                        if check not in foundstrings:
                            common.logDebug("Found string at", pos)
                            foundstrings.append(check)
                            out.write(check + "=\n")
                        pos = f.tell() - 1
                f.seek(pos + 1)
    common.logMessage("Done! Extracted", len(foundstrings), "lines")
