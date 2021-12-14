import Character
import Settlement


class Faction:
    """
    Represents the attributes (and text entry) of a faction, including its settlements, characters, culture, and
    campaign details.

    """
    def __init__(self):
        self.name = ""
        self.cult = ""
        self.settlements = []
        self.characters = []
        self.text = ""
