import os
import re
from numpy import random as rand
rand.seed(1)


class GarrisonGenerator:
    """
    Contains values & functions for generating culture-specifc garrisons.
    Uses a points-based system based on settlement tier to ensure starting armies are interesting and difficult.

    """
    def __load_templates__(self):
        """
        Loads the starting templates for each faction

        :return:
        """
        filepath = "defaults/armies/"
        templates = os.listdir(filepath)
        factions = []
        for file in templates:
            army = open(filepath + file)
            army = army.read()
            army = re.split(r"#[A-Z]+\n", army)
            units = []
            for rank in army[1:]:
                rank_units = re.split(r"\n", rank)
                rank_units = rank_units[:-1] if len(rank_units) > 1 else rank_units
                units.append(rank_units)
            factions.append(units)
        self.facnames = [t.replace(".txt", "") for t in templates]
        self.templates = factions

    def generate_garrisons(self, fac, tier):
        """
        Generates a garrison given the provided statistics, faction, and settlement rank

        :param fac: faction to generate for
        :param tier: level of the assigned settlement
        :return: array of units to add to the garrison
        """
        allowed = self.templates[self.facnames.index(fac)]  # allowed units
        tier_num = self.CITY_TIERS.index(tier)  # tier converted to a numerical representation

        points = self.pts_def + (self.pts_per * tier_num)
        garrison = []

        # First add Rares
        rares = []
        for i in range(self.max_rare[tier_num]):
            if rand.random() > 0.85 or points < self.costs[2]:  # Some degree of uncertainty; the max allowed shouldn't always be used
                break
            else:
                rares.append(rand.choice(allowed[2], 1)[0])
                points -= self.costs[2]
        rares = sorted(rares)
        garrison.extend(rares)

        # Then add Uncommons
        unc = []
        for i in range(self.max_uncommon[tier_num]):
            if rand.random() > 0.95 or points < self.costs[1]:  # Some degree of uncertainty; the max allowed shouldn't always be used
                break
            else:
                unc.append(rand.choice(allowed[1], 1)[0])
                points -= self.costs[1]
        unc = sorted(unc)
        garrison.extend(unc)

        # Round it out with standards
        c = []
        c.extend(rand.choice(allowed[0], points, replace=True))
        c = sorted(c)
        garrison.extend(c)

        # Append & return
        return garrison

    def __init__(self):
        self.pts_def = 6  # starting capacity at villages
        self.pts_per = 2  # additional points per settlement level
        self.costs = [1, 2, 3]  # costs for each unit rank
        self.max_uncommon = [1, 1, 2, 3, 4, 5]  # for village, town, large town, city, large city, huge city
        self.max_rare = [0, 0, 0, 1, 2, 3]
        self.facnames = []  # loaded in __load_templates_()
        self.templates = []
        self.CITY_TIERS = ['village', 'town', 'large_town', 'city', 'large_city', 'huge_city']
