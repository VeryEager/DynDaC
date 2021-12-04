import re
from numpy import random as rand
from PIL import Image, ImageOps

# Global File Parameters
rand.seed(1)
PATH = "campaign/"

# Global Generation Parameters
MONEY_MIN = 5000
MONEY_MAX = 15000
PURSE_MIN = 3
PURSE_MAX = 7.5
CITIES_PER = 1

# Load relevant TXT files
d_strat = open(PATH + "descr_strat.txt", "r")
d_strat = d_strat.read()
d_regions = open(PATH + "descr_regions.txt", "r")
d_regions = d_regions.read()

# Load TGA maps
m_regions = Image.open(PATH + "map_regions.tga")  # Need for settlement location information
m_regions = ImageOps.flip(m_regions)
m_ground_types = Image.open(PATH + "map_ground_types.tga")  # To track valid/invalid tiles
m_ground_types = ImageOps.flip(m_ground_types)


def split_strat_fac(desc_strat):
    """
    Splits the loaded descr_strat file into factions

    :return: Campaign Info, Faction details[], Diplomacy
    """
    by_fac = re.split(r"(\bfaction\s[a-z]+)|(\bStandings)", desc_strat)
    by_fac = [s for s in by_fac if s is not None]
    by_fac_flat = [x[0]+x[1] for x in zip(by_fac[1::2], by_fac[2::2])]
    return by_fac[0], by_fac_flat[:-1], by_fac[len(by_fac)-1]


def split_strat_reg_char(faction):
    """
    Splits the found faction details into regions & characters

    :param faction:
    :return: Faction Info, Settlements[], Characters[], Family
    """
    strat = re.split(r"(\bsettlement)|(\bcharacter\s)", faction)
    info = [s for s in strat if s is not None]
    info = [x[0]+x[1] for x in zip(info[1::2], info[2::2])]

    family = info[-1].split("character_record", 1)  # Save info on family relationships
    info[-1] = family[0]
    if len(family) > 1:                                   # To Account for some factions not having family trees
        family = "character_record" + family[1]
    else:
        family = ""

    settlements = [s for s in info if "character" not in s]  # Split into provinces/characters respectively
    characters = [s for s in info if "settlement" not in s]
    characters = [s for s in characters if "admiral" not in s]  # also need to drop admirals

    return strat[0], settlements, characters, family


# Split descr_strat into faction sections & diplomacy/campaign
Campaign, Split_Factions, Diplomacy = split_strat_fac(d_strat)
Invariants = Split_Factions[-3:-1]  # Some factions shouldn't change positions (dark lord, scripts, etc)
del Split_Factions[-3]
del Split_Factions[-2]

# Subdivide factions into global pool of settlements & faction-specific details (family trees, armies, etc)
Factions = []
Settlements = []
for faction in Split_Factions:
    details = split_strat_reg_char(faction)
    Settlements.extend(details[1])
    Factions.append([details[0], details[2], details[3]])


def assign_settlements(s, f):
    """
    Assign random starting locations to each faction

    :param s: Settlements
    :param f: Factions
    :return:
    """
    remaining_s = s

    for faction in f[:-1]:
        capital = rand.choice(remaining_s, 1)
        del remaining_s[remaining_s.index(capital)]
        faction.append(capital)

    # Add all remaining settlements to rebels
    f[-1].append(remaining_s)


def name_from_text(text):
    """
    Parses the name of a region from its descr_strat entry

    :param text: original descr_start text
    :return: string form of the region's name
    """
    region = re.split(r"(\bregion\s(?i)[a-z_]+Province)", text)
    region = region[1].split()
    return region[1]


def colour_from_name(name):
    """
    Retrieves the colour pf a region from its name via descr_regions

    :param name: name of the province
    :return: RGB of the province on map_regions
    """
    non_legion = r"}\n\s*" + name + "|^" + name  # non-legion regex
    parsed = re.split(non_legion, d_regions)
    parsed = re.split(r"([0-9]+\s[0-9]+\s[0-9]+\s)", parsed[1])
    r, g, b = parsed[1].split()
    return int(r), int(g), int(b)


def pixel_map(mp):
    """
    Extracts the pixel values from the TGA file

    :param mp: the map to extract the values from
    :return:
    """
    width, height = mp.size
    mp = mp.load()

    pixels = []
    for x in range(width):
        row = []
        for y in range(height):
            pixel = mp[x, y]
            row.append(pixel[0:3])
        pixels.append(row)
    return pixels


def find_settlement_coords(colour, mp):
    """
    Identifies the X,Y coord vector given a region colour & regions map

    :param colour: RGB colour of the desired region
    :param mp: region map, should be preprocessed using pixel_map
    :return:
    """
    # TODO: HIGHLY INEFFICIENT; BETTER SEARCHING ALGORITHM REQ'D
    x, y = (0, 0)
    for indr, row in enumerate(mp):
        for indp, pix in enumerate(row):
            if pix == (0, 0, 0):
                if mp[indr][indp-1] == colour or mp[indr][indp+1] == colour:
                    x = indr
                    y = indp
    return x, y


def tile_is_valid(x, y, mp):
    """
    Ensures a chosen tile is valid to be placed on provided the terrain is adequate

    :param x:
    :param y:
    :param mp:
    :return:
    """
    return


def assign_chars(f):
    """
    Assigns starting locations for characters to be centered around the faction's starting settlement

    :param f: Factions
    :return:
    """
    for fac in f[:-1]:
        capital = find_settlement_coords(colour_from_name(name_from_text(fac[3][0])), pixel_map(m_regions))
        new_chars = []
        for ch in fac[1]:
            if "leader," in ch:
                ch = re.sub(r"(x\s[0-9]+,\sy\s[0-9]+)", "x " + str(capital[0]) + ", y " + str(capital[1]), ch)
            else:
                offset = rand.randint(-10, 10, 2)
                pos = capital + offset
                ch = re.sub(r"(x\s[0-9]+,\sy\s[0-9]+)", "x " + str(pos[0]) + ", y " + str(pos[1]), ch)
            new_chars.append(ch)
        fac[1] = new_chars  # Add changed character locations


def write(c, f, d):
    """
    Writes the generated scenario to descr_strat

    :param c: Campaign Information
    :param f: Faction Information
    :param d: Diplomacy Information
    :return:
    """
    descr_strat = open("descr_strat.txt", "a")
    descr_strat.write(c)
    descr_strat.write("".join(Invariants))

    for fac in f:
        text_sett = "".join(fac[3])
        text_char = "".join(fac[1])
        descr_strat.write(fac[0]+text_sett+text_char+fac[2])

    descr_strat.write(d)


# Re-assign starting locations & export
assign_settlements(Settlements, Factions)
assign_chars(Factions)
write(Campaign, Factions, Diplomacy)
