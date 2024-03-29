import os
import click
import game
from hacktools import common, nds, nitro

version = "1.5.1"
romfile = "gurren.nds"
rompatch = "data/gurren_patched.nds"
bannerfile = "data/repack/banner.bin"
patchfile = "data/patch.xdelta"
infolder = "data/extract/"
replacefolder = "data/replace/"
outfolder = "data/repack/"


@common.cli.command()
@click.option("--rom", is_flag=True, default=False)
@click.option("--bin", is_flag=True, default=False)
@click.option("--3dg", "tdg", is_flag=True, default=False)
@click.option("--kpc", is_flag=True, default=False)
@click.option("--spc", is_flag=True, default=False)
@click.option("--vsc", is_flag=True, default=False)
@click.option("--yce", is_flag=True, default=False)
def extract(rom, bin, tdg, kpc, spc, vsc, yce):
    all = not rom and not bin and not tdg and not kpc and not spc and not vsc and not yce
    if all or rom:
        nds.extractRom(romfile, infolder, outfolder)
        # Extract NFP archives
        nfpin = "data/extract/data/"
        nfpout = "data/extract_NFP/"
        nfpwork = "data/work_NFP/"
        common.logMessage("Extracting NFP ...")
        common.makeFolder(nfpout)
        files = common.getFiles(nfpin, ".NFP")
        for file in common.showProgress(files):
            common.logDebug("Processing", file, "...")
            common.makeFolder(nfpout + file)
            with common.Stream(nfpin + file, "rb") as f:
                f.seek(52)  # Header: NFP2.0 (c)NOBORI 1997-2006
                filenum = f.readInt()
                f.seek(4, 1)  # Always 0x50
                datastart = f.readInt()
                f.seek(16, 1)  # All 0
                common.logDebug("Found", filenum, "files, data starting at", datastart)
                for i in range(filenum):
                    # Filenames are always 16 bytes long, padded with 0s
                    subname = f.readString(16)
                    # Read starting position and size (multiplied by 4)
                    startpos = f.readInt()
                    size = f.readInt() // 4
                    # Extract the file
                    common.logDebug("Extracting", subname, "starting at", startpos, "with size", size)
                    savepos = f.tell()
                    f.seek(startpos)
                    with common.Stream(nfpout + file + "/" + subname, "wb") as newf:
                        newf.write(f.read(size))
                    f.seek(savepos)
        # Copy everything to the work folder
        common.copyFolder(nfpout, nfpwork)
        common.logMessage("Done! Extracted", len(files), "archives")
    if all or bin:
        import extract_bin
        extract_bin.run()
    if all or tdg:
        nitro.extractNSBMD("data/extract_NFP/NFP3D.NFP/", "data/out_3DG/", ".3DG", readfunc=game.read3DG)
    if all or kpc:
        import extract_kpc
        extract_kpc.run()
    if all or spc:
        import extract_spc
        extract_spc.run()
    if all or vsc:
        import extract_vsc
        extract_vsc.run()
    if all or yce:
        for i in range(1, 8):
            common.copyFile("data/extract_NFP/NFP2D.NFP/AV01_0" + str(i) + ".YCE", "data/extract_NFP/NFP2D.NFP/AV00_0" + str(i) + ".YCE")
        import extract_yce
        extract_yce.run()


@common.cli.command(hidden=True)
@click.argument("file")
@click.option("--p", is_flag=True, default=False)
def analyze(file, p):
    import analyze_spc
    analyze_spc.run(file, p)


@common.cli.command(hidden=True)
@click.argument("file")
@click.option("--n", default=0)
def expand(file, n):
    import expand_yce
    expand_yce.run(file, n)


@common.cli.command()
@click.option("--no-rom", is_flag=True, default=False, hidden=True)
@click.option("--bin", is_flag=True, default=False)
@click.option("--3dg", "tdg", is_flag=True, default=False)
@click.option("--kpc", is_flag=True, default=False)
@click.option("--spc", is_flag=True, default=False)
@click.option("--vsc", is_flag=True, default=False)
@click.option("--yce", is_flag=True, default=False)
@click.option("--deb", is_flag=True, default=False, hidden=True)
@click.option("--force", default="", hidden=True)
@click.option("--analyze", default="", hidden=True)
def repack(no_rom, bin, tdg, kpc, spc, vsc, yce, deb, force, analyze):
    all = not bin and not tdg and not kpc and not spc and not vsc and not yce
    if all or bin or spc:
        import repack_font
        repack_font.run()
    if all or bin:
        import repack_bin
        repack_bin.run()
        common.armipsPatch("bin_patch.asm")
    if all or tdg:
        common.copyFile("data/extract_NFP/NFP3D.NFP/MSW_C053.3DG", "data/extract_NFP/NFP3D.NFP/MSW_C083.3DG")
        game.repackNSBMD("data/work_3DG/", "data/extract_NFP/NFP3D.NFP/", "data/work_NFP/NFP3D.NFP/", ".3DG", writefunc=game.write3DG)
        import patch_jnt
        patch_jnt.run()
    if all or kpc:
        import repack_kpc
        repack_kpc.run()
    if all or spc:
        import repack_spc
        repack_spc.run()
    if all or vsc:
        import repack_vsc
        repack_vsc.run()
    if all or yce:
        import repack_yce
        repack_yce.run()

    if not no_rom:
        debfolder = "data/extract_NFP/"
        nfpin = "data/extract/data/"
        nfpwork = "data/work_NFP/"
        nfpout = "data/repack/data/"
        # Debug map
        if deb:
            common.copyFile(debfolder + "SPC.NFP/S_DEBUG.SPC", nfpwork + "SPC.NFP/S_MAIN.SPC")
        else:
            common.copyFile(debfolder + "SPC.NFP/S_MAIN.SPC", nfpwork + "SPC.NFP/S_MAIN.SPC")
        if force != "":
            common.copyFile(nfpwork + "SPC.NFP/" + force + ".SPC", nfpwork + "SPC.NFP/SYS_000.SPC")
        # Repack NFP archives
        if os.path.isdir(replacefolder):
            common.mergeFolder(replacefolder, nfpwork)
        common.logMessage("Repacking NFP ...")
        files = common.getFiles(nfpin, ".NFP")
        for file in common.showProgress(files):
            subfiles = os.listdir(nfpwork + file)
            filenum = len(subfiles)
            # Data starts at header (80 bytes) + entries (24 bytes each)
            datapos = 80 + (24 * filenum)
            # The file list is padded with 0s if it doesn't start at a multiple of 16
            datapos += datapos % 16
            common.logDebug("Repacking", file, "with", filenum, "files ...")
            with common.Stream(nfpout + file, "wb") as f:
                f.writeString("NFP2.0 (c)NOBORI 1997-2006")
                f.writeZero(26)
                f.writeInt(filenum)
                f.writeInt(0x50)
                f.writeInt(datapos)
                for i in range(filenum):
                    subfile = subfiles[i]
                    subfilepath = nfpwork + file + "/" + subfile
                    filesize = os.path.getsize(subfilepath)
                    f.seek(80 + (24 * i))
                    f.writeString(subfile)
                    if len(subfile) < 16:
                        f.writeZero(16 - len(subfile))
                    f.writeInt(datapos)
                    f.writeInt(filesize * 4)
                    f.seek(datapos)
                    with open(subfilepath, "rb") as newf:
                        f.write(newf.read(filesize))
                    datapos += filesize
        # Edit banner and repack ROM
        nds.editBannerTitle(bannerfile, "Tengen Toppa\nGurren Lagann\nKonami Digital Entertainment")
        nds.repackRom(romfile, rompatch, outfolder, patchfile)


if __name__ == "__main__":
    common.setupTool("GurrenTranslation", version, "data", romfile, 0x6eac24b8)
