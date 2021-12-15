# Contains various text-related functions to extract information from descr_strat & descr_regions
import re


def faction_name_from_strat(text):
    """
    Parses the name of the faction from descr_strat entry

    :param text: text entry to retrieve the name from
    :return: string of the faction's internal name
    """
    spl = re.split(r"faction\s([a-z|_]+),", text)
    return spl[1]


def character_name_from_strat(text):
    """
    Extracts a character's name from text

    :param text: character entry in descr_strat
    :return: string of the character's name
    """
    spl = re.split(r"\t([A-Z]+[a-z]+),", text)
    return spl[1]


def settlement_name_from_strat(text):
    """
    Parses the name of a region from its descr_strat entry

    :param text: original descr_start text
    :return: string form of the region's name
    """
    region = re.split(r"(\bregion\s(?i)[a-z_]+Province)", text)
    region = region[1].split()
    return region[1]


def settlement_tier_from_strat(text):
    """
    Parses the tier of a settlement from its descr_strat entry

    :param text: original descr_strat text
    :return: string form of the settlement tier
    """
    settlement = re.split(r"level\s([a-z|_]+)\n", text)
    return settlement[1]


def region_colour_from_name_regions(name, regions):
    """
    Retrieves the colour of a region from its name via descr_regions

    :param regions: descr_regions text
    :param name: name of the province
    :return: RGB of the province on map_regions
    """
    non_legion = r"}\n\s*" + name + "|^" + name  # non-legion regex
    parsed = re.split(non_legion, regions)
    parsed = re.split(r"([0-9]+\s[0-9]+\s[0-9]+\s)", parsed[1])
    r, g, b = parsed[1].split()
    return int(r), int(g), int(b)


def settlement_culture_from_regions(name, regions):
    """
    Retrieves the starting cultures from a region via descr_regions

    :param regions: descr_regions text
    :param name: name of the region
    :return: array containing the culture distribution
    """
    non_legion = r"}\n\s*" + name + "|^" + name  # non-legion regex
    parsed = re.split(non_legion, regions)
    parsed = re.split(r"religions\s{\s([a-z|\s|_|[0-9]+)\s}", parsed[1])
    cults = parsed[1].split()
    return cults


def character_location_from_strat(text):
    """
    Extracts the coordinate vector (x,y) from a character's descr_strat entry

    :param text: The text to parse
    :return:
    """
    loc = re.split(r"(x\s[0-9]+,\sy\s[0-9]+)", text)[1]
    return loc


def split_factions_in_strat(text):
    """
    Splits the loaded descr_strat file into factions

    :return: Campaign Info, Faction details[], Diplomacy
    """
    by_fac = re.split(r"(\bfaction\s[a-z]+)|(\bStandings)", text)
    by_fac = [s for s in by_fac if s is not None]
    by_fac_flat = [x[0]+x[1] for x in zip(by_fac[1::2], by_fac[2::2])]
    return by_fac[0], by_fac_flat[:-1], by_fac[len(by_fac)-1]


def split_factions_by_details_strat(faction):
    """
    Splits faction details into settlements, characters, and constants

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


def faction_culture_from_sm_factions(sm_factions, facname):
    rel = re.split(r"faction\s+" + facname + r"\n[a-z|\s|_]+\nreligion\s+([a-z]+)\n", sm_factions)
    rel = rel[1]
    return rel
