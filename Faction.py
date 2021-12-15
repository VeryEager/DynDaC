import Character
import Settlement
from text_extraction import faction_name_from_strat


class Faction:
    """
    Represents the attributes (and text entry) of a faction, including its settlements, characters, culture, and
    campaign details.

    """
    def __init__(self, text):
        self.name = ""
        self.cult = ""
        self.start_money = 0
        self.kings_purse = 0
        self.settlements = []  # First settlement is always capital
        self.characters = []  # First character SHOULD always be faction leader
        self.text = text

    def parse_text(self):
        """
        Parses the raw text of the Faction entry

        :return:
        """
        return None
