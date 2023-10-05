NoMod = 0
NoFail = 1
Easy = 2
TouchDevice = 4
Hidden = 8
HardRock = 16
SuddenDeath = 32
DoubleTime = 64
Relax = 128
HalfTime = 256
Nightcore = 512
Flashlight = 1024
SpunOut = 4096
AutoPilot = 8192
Perfect = 16384


def get_mods(magic_number):
    mods = []
    if magic_number & SpunOut:
        mods.append("SO")
    if magic_number & Easy:
        mods.append("EZ")
    if magic_number & Nightcore:
        mods.append("NC")
    if magic_number & HalfTime:
        mods.append("HT")
    if magic_number & Hidden:
        mods.append("HD")
    if magic_number & DoubleTime:
        mods.append("DT")
    if magic_number & HardRock:
        mods.append("HR")
    if magic_number & Flashlight:
        mods.append("FL")
    if magic_number & TouchDevice:
        mods.append("TD")
    if magic_number & SuddenDeath:
        mods.append("SD")
    if magic_number & NoFail:
        mods.append("NF")
    if magic_number & Perfect:
        mods.append("PF")
    if magic_number & Relax:
        mods.append("RX")
    return mods


def mods_from_string(mods_str):
    mods_str = mods_str.upper()
    if not mods_str or mods_str == "NM":
        return 0
    mods = 0
    if "NF" in mods_str:
        mods += NoFail
    if "EZ" in mods_str:
        mods += Easy
    if "TD" in mods_str:
        mods += TouchDevice
    if "HD" in mods_str:
        mods += Hidden
    if "HR" in mods_str:
        mods += HardRock
    if "SD" in mods_str:
        mods += SuddenDeath
    if "DT" in mods_str:
        mods += DoubleTime
    if "RX" in mods_str:
        mods += Relax
    if "HT" in mods_str:
        mods += HalfTime
    if "NC" in mods_str:
        mods += Nightcore
    if "FL" in mods_str:
        mods += Flashlight
    if "SO" in mods_str:
        mods += SpunOut
    if "AP" in mods_str:
        mods += AutoPilot
    if "PF" in mods_str:
        mods += Perfect
    return mods


def get_mods_simple(magic_number):
    mods = get_mods(magic_number)
    if "NC" in mods:
        mods.remove("DT")
    if "PF" in mods:
        mods.remove("SD")
    return mods


def convert_mods(magic_number):
    new = magic_number
    if magic_number & Nightcore:
        new -= Nightcore
    if magic_number & SpunOut:
        new -= SpunOut
    if magic_number & SuddenDeath:
        new -= SuddenDeath
    if magic_number & NoFail:
        new -= NoFail
    if magic_number & TouchDevice:
        new -= TouchDevice
    if magic_number & Perfect:
        new -= Perfect
    return new
