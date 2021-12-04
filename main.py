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
strat = open(PATH + "descr_strat.txt", "r")
strat = strat.read()

# Load TGA maps
regions = Image.open(PATH+"map_regions.tga")  # Need for settlement location information
regions = ImageOps.flip(regions)
ground_types = Image.open(PATH+"map_ground_types.tga")  # To track valid/invalid tiles
ground_types = ImageOps.flip(ground_types)


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
    split = re.split(r"(\bsettlement)|(\bcharacter\s)", faction)
    info = [s for s in split if s is not None]
    info = [x[0]+x[1] for x in zip(info[1::2], info[2::2])]

    family = info[-1].split("character_record", 1)  # Save info on family relationships
    info[-1] = family[0]
    if len(family) > 1:                                   # To Account for some factions not having family trees
        family = "character_record" + family[1]
    else:
        family = ""

    # TODO: Drop Admirals

    settlements = [s for s in info if "character" not in s]  # Split into provinces/characters respectively
    characters = [s for s in info if "settlement" not in s]

    return split[0], settlements, characters, family


# Split descr_strat into faction sections & diplomacy/campaign
Campaign, Split_Factions, Diplomacy = split_strat_fac(strat)
Invariants = Split_Factions[-3:-1]
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
        remaining_s = [i for i in remaining_s if i is not capital]
        faction.append(capital)

    # Add all remaining settlements to rebels
    f[-1].append(remaining_s)


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

    for faction in f:
        text_sett = "".join(faction[3])
        text_char = "".join(faction[1])
        descr_strat.write(faction[0]+text_sett+text_char+faction[2])

    descr_strat.write(d)


# Re-assign starting settlements & export
assign_settlements(Settlements, Factions)
write(Campaign, Factions, Diplomacy)
