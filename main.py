import re
import time

from math import ceil
from GarrisonGenerator import GarrisonGenerator
from numpy import random as rand
from PIL import Image, ImageOps
from text_extraction import faction_name_from_strat, character_name_from_strat, settlement_name_from_strat, \
    settlement_tier_from_strat, region_colour_from_name_regions, settlement_culture_from_regions, \
    character_location_from_strat, split_factions_in_strat, split_factions_by_details_strat, \
    faction_culture_from_sm_factions

# Global File Parameters
rand.seed(43)
PATH = "campaign/"

# Global Constants
# map_ground_types
COL_MOUNT = (98, 65, 65)
COL_IMPASS = (64, 64, 64)
COL_SHALLOW = (196, 0, 0)
COL_DEEP = (64, 0, 0)
COL_DENSE = (0, 64, 0)
# map_regions
COL_SEA = (41, 140, 233)
COL_SETTLE = (0, 0, 0)
COL_PORT = (255, 255, 255)
# map_features
COL_FEATURELESS = (0, 0, 0)

# Global Generation Parameters
FUNDS_DEF = 5000
FUNDS_PER = 1000  # Starting gold per starting char
PURSE_DEF = 500
PURSE_PER = 250  # Extra per-turn income per starting char
CITIES_PER = 1
STARTING_CULT = 33  # Starting religion of faction's capital province
REMOVE_GENERALS = True

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
m_rivers = Image.open(PATH + "map_features.tga")  # For invalid river tiles
m_rivers = ImageOps.flip(m_rivers)


# Split descr_strat into faction sections & diplomacy/campaign
Campaign, Split_Factions, Diplomacy = split_factions_in_strat(d_strat)
Invariants = Split_Factions[-3:-1]  # Some factions shouldn't change positions (dark lord, scripts, etc)
del Split_Factions[-3]
del Split_Factions[-2]

# Subdivide factions into global pool of settlements & faction-specific details (family trees, armies, etc)
Factions = []
Settlements = []  # all settlements in the map
OrigSettlements = []  # original settlements assigned to each faction
set = 0
for faction in Split_Factions:
    details = split_factions_by_details_strat(faction)
    Settlements.extend(details[1])
    set += len(details[1]) if "slave" not in details[0] else 0
    Factions.append([details[0], details[2], details[3]])
    if "slave" not in details[0]:
        OrigSettlements.append(details[1])  # don't include slave in original settlements


def assign_settlements(settlements, factions):
    """
    Assign random starting locations to each faction

    :param settlements: Settlements
    :param factions: Factions
    :return:
    """
    remaining_s = settlements

    for fac in factions[:-1]:
        capital = rand.choice(remaining_s, 1)
        del remaining_s[remaining_s.index(capital)]
        fac.append(capital)

    # Add all remaining settlements to rebels
    factions[-1].append(remaining_s)


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
            if pix == COL_SETTLE:
                if mp[indr][indp-1] == colour or mp[indr][indp+1] == colour or mp[indr-1][indp] == colour \
                        or mp[indr+1][indp] == colour:
                    x = indr
                    y = indp
    return x, y


def get_surrounding_tiles(x, y):
    """
    Retrieves the X, Y coords of the 8 tiles surrounding some point

    :param x:
    :param y:
    :return:
    """
    tiles = [(-1, -1), (-1, 0), (-1, 1),
            (0, -1), (0, 0), (0, 1),
            (1, -1), (1, 0), (1, 1)]
    tiles = [(t[0]+x, t[1]+y) for t in tiles]
    return tiles


def tile_is_valid(x, y, facs, self_fac, strat):
    """
    Ensures a chosen tile is valid to be placed on provided the terrain is adequate

    :param x: x coord
    :param y: y coord
    :param mp: Pixel map of map_ground_types
    :param facs: Faction starting location details
    :param self_fac: Own Faction, consisting of changed parameters.
    :param strat: Strat details (watchtowers, forts, etc)
    :return: True if position is available, False otherwise
    """
    # TODO: again, horribly inefficient. just enumerates all known positions
    for tile in get_surrounding_tiles(x, y):
        if re.search(r"" + str(tile[0]) + r"\s" + str(tile[1]), strat) is not None:
            return False    # if fort/watchtower is on the position

    for fac in facs[:-1]:  # don't bother with rebel overlap
        for ch in fac[1]:
            if re.search(r"x\s" + str(x) + r",\sy\s" + str(y), ch) is not None:
                return False  # characters from different factions shouldn't overlap
            # TODO: side effect, chars can't be put @ original pos's of their own faction

    for ch in self_fac:
        if re.search(r"x\s" + str(x) + r",\sy\s" + str(y), ch) is not None:
            return False  # characters in same faction shouldn't overlap

    p_gts = pixel_map(m_ground_types)
    p_regions = pixel_map(m_regions)
    p_rivers = pixel_map(m_rivers)

    if p_regions[x][y] == COL_SETTLE or p_regions[x][y] == COL_SEA:
        return False  # can't be on another settlement, nor the ocean

    if p_rivers[x][y] != COL_FEATURELESS:
        return False  # chars shouldn't be on mt doom, rivers, etc

    gts = [p_gts[x*2][y*2], p_gts[x*2+1][y*2+1], p_gts[x*2+1][y*2], p_gts[x*2][y*2+1]]
    if COL_SHALLOW in gts or COL_DEEP in gts or COL_DENSE in gts or COL_IMPASS in gts or COL_MOUNT in gts:
        # TODO: check if this actually finds the correct tile
        return False  # chars can't be placed in wrong-terrain tiles

    return True


def get_names(fac):
    """
    Retrieves valid names for characters (those which aren't found in descr_strat)

    :param fac: entry for the faction
    :return:
    """
    name = faction_name_from_strat(fac[0])
    possible = open("descr_names.txt", "r")
    possible = possible.read()
    possible = re.split(r"faction:\s" + name + r"[\s]+characters[\s]+([a-z|\s|_]+)women", possible, flags=re.IGNORECASE)
    possible = re.split(r"[\s]+", possible[1])
    used_names = [character_name_from_strat(ch) for ch in fac[1]]
    possible = [n for n in possible[:-1] if n not in used_names and n not in fac[2]]
    return possible


def add_agents(typ, facs):
    """
    Adds the corresponding type of agent to a faction if the faction lacks

    :param typ: Type of agent (spy, diplomat)
    :param facs: Factions
    :return:
    """
    for fac in facs:
        agent_file = open("defaults/" + typ + ".txt", "r")  # default diplomat
        agent = agent_file.read()
        has = False
        for ch in fac[1]:
            if typ in ch:
                has = True  # ignore factions with the agent
        if not has:
            name = rand.choice(get_names(fac))
            agent = re.sub(r"NAME", name, agent)
            fac[1].append(agent)


def assign_chars(f):
    """
    Assigns starting locations for characters to be centered around the faction's starting settlement

    :param f: Factions
    :return:
    """
    for fac in f[:-1]:
        capital = find_settlement_coords(region_colour_from_name_regions(settlement_name_from_strat(fac[3][0]), d_regions), pixel_map(m_regions))
        new_chars = []
        for ch in fac[1]:
            if "leader," in ch:  # don't need to check availability for leaders; always in a settlement
                ch = re.sub(r"(x\s[0-9]+,\sy\s[0-9]+)", "x " + str(capital[0]) + ", y " + str(capital[1]), ch)
            else:
                offset = rand.randint(-10, 10, 2)
                pos = capital + offset
                while not tile_is_valid(pos[0], pos[1], Factions, new_chars, Diplomacy):
                    offset = rand.randint(-10, 10, 2)
                    pos = capital + offset
                ch = re.sub(r"(x\s[0-9]+,\sy\s[0-9]+)", "x " + str(pos[0]) + ", y " + str(pos[1]), ch)
            new_chars.append(ch)
        fac[1] = new_chars  # Add changed character locations


def garrisons_to_abandoned():
    """
    Assigns culture-appropriate garrisons to rebel settlements.

    :return:
    """
    gen = GarrisonGenerator()
    gen.__load_templates__()

    new_chars = []
    for i, settles in enumerate(OrigSettlements):
        fac = faction_name_from_strat(Factions[i][0])
        for city in settles:
            used = False
            for fact in Factions[:-1]:
                if city in fact[3]:
                    used = True

            if not used:  # if the abandoned settlement is not in use by any faction then we add rebel army
                template = open("defaults/rebel_army.txt")
                template = template.read()
                template = re.sub(r"#FAC#", fac, template)

                tier = settlement_tier_from_strat(city)
                new_army = gen.generate_garrisons(fac, tier)

                for unit in new_army:
                    template += unit + "\n"
                template += "\n"

                # now we update the x, y of the new army
                pos = find_settlement_coords(region_colour_from_name_regions(settlement_name_from_strat(city), d_regions), pixel_map(m_regions))
                template = re.sub(r"(x\s[0-9]+,\sy\s[0-9]+)", "x " + str(pos[0]) + ", y " + str(pos[1]), template)
                new_chars.append(template)
    Factions[-1][1].extend(new_chars)


def update_funds():
    """
    Naively adjusts funds based on number of characters in faction

    :return:
    """
    for fac in Factions[:-1]:
        chars = len(fac[1])+1   # Obtain starting number of chars
        new_funds = "denari\t" + str(FUNDS_DEF+chars*FUNDS_PER) + "\ndenari_kings_purse\t" + str(PURSE_DEF+chars*PURSE_PER)
        funds = re.sub(r"(denari\s+[0-9]+\s*\n\s*denari_kings_purse\s+[0-9]+)", new_funds, fac[0])
        fac[0] = funds


def update_culture(facs):
    """
    Ensures factions have some amount of starting culture in their new capital

    :param facs: All factions to update cultures for
    :return:
    """
    new_cults = []
    for fac in facs:
        facname = faction_name_from_strat(fac[0])

        # Split at the faction
        sm_factions = open("descr_sm_factions.txt", "r")
        sm_factions = sm_factions.read()
        rel = faction_culture_from_sm_factions(sm_factions, facname)

        # Get the current cultures for the capital city & their strengths
        cults = settlement_culture_from_regions(settlement_name_from_strat(fac[3][0]), d_regions)
        cult_strengths = cults[1::2]
        cult_strengths = [int(s) for s in cult_strengths]
        cults = cults[0::2]

        # Reduce each active culture by an assigned proportion.
        active_cults = sum([1 for i in cult_strengths if i != 0])
        ratio = ceil(STARTING_CULT/active_cults)
        remaining = STARTING_CULT
        to_reduce = cult_strengths.index(max(cult_strengths))
        cult_strengths[to_reduce] -= remaining
        cult_strengths[cults.index(rel)] += remaining
        remaining -= remaining

        to_replace = []  # update the array to export to doc
        for pos in range(len(cults)):
            to_replace.append(cults[pos])
            to_replace.append(str(cult_strengths[pos]))
        new_cults.append(to_replace)
    return new_cults


def disable_overlapping_armies(target, Facs):
    """
    Removes all armies from faction target which overlap with a force from any other faction

    :param target: Target faction
    :param Facs: remaining factions
    :return:
    """
    new_chs = []
    for ch in target[1]:
        overlap = False
        for fac in Facs:
            for fch in fac[1]:
                ch_loc = character_location_from_strat(ch).strip()
                fch_loc = character_location_from_strat(fch).strip()
                if ch_loc == fch_loc:
                    overlap = True
        if not overlap:
            new_chs.append(ch)  # only use armies who have NO overlap
    target[1] = new_chs


def write_regions(cults, facs):
    """
    Writes the new culture ratios to descr_regions

    :param facs: Factions to update the capitals for
    :param cults: new cultures to replace the old cultures
    :return:
    """
    descr_regions = open("descr_regions.txt", "a")

    # First split orig file into regions
    regions = re.split(r"(}\n\s*[a-z|A-Z|_]+|^[a-z|A-Z|_]+)", d_regions)

    # Then for/e actual capital, update the corresponding capital influences
    for cult, fac in zip(cults, facs):
        capital = fac[3][0]
        name = settlement_name_from_strat(capital)
        if name != 'North_Enedwaith_Province':  # hardcoded to match the first province. yelch.
            loc = regions.index("}\n" + name) + 1
        else:
            loc = 2
        regions[loc] = re.sub(r"({[\s|a-z|0-9|_]+)", "{ " + " ".join(cult) + " ", regions[loc])

    text = "".join(regions)
    descr_regions.write(text)


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

    descr_strat.write(";" + d)


start = time.time()
pixel_gts = pixel_map(m_ground_types)
# Re-assign starting locations & export
add_agents("diplomat", Factions[:-1])
assign_settlements(Settlements, Factions)
cultures = update_culture(Factions[:-1])
assign_chars(Factions)
disable_overlapping_armies(Factions[-1], Factions[:-1])
garrisons_to_abandoned()
update_funds()
write(Campaign, Factions, Diplomacy)
write_regions(cultures, Factions[:-1])
print("EXECUTION TIME: ", round(time.time()-start, 2), "s")
