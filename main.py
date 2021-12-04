import re
from PIL import Image, ImageOps

# Global File Parameters
PATH = "campaign/"

# Global Generation Parameters
PURSE_MIN = 3
PURSE_MAX = 7.5

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

    :return: Campaign Info, Faction details, Diplomacy
    """
    by_fac = re.split(r"(\bfaction\s[a-z]+)|(\bStandings)", desc_strat)
    by_fac = [s for s in by_fac if s is not None]
    by_fac_flat = [x[0]+x[1] for x in zip(by_fac[1::2], by_fac[2::2])]
    return by_fac[0], by_fac_flat[:-1], by_fac[len(by_fac)-1]


def split_strat_reg_char(faction):
    """
    Splits the found faction details into settlements & characters

    :param faction:
    :return: both the faction details & the settlement entries
    """
    split = re.split(r"", faction)
    provinces = []
    characters = []

    return


# Split descr_strat into factions, regions, armies, etc
Campaign, Factions, Diplomacy = split_strat_fac(strat)
Invariants = Factions[-3:-1]
del Factions[-3]
del Factions[-2]


