
class Settlement:
    """
    Represents a settlement/region on the campaign map, including the region colour, settlement coordinates, settlement
    cultures & name.

    """
    def __init__(self):
        self.colour = (0, 0, 0)
        self.name = ""
        self.settlement_location = (0, 0)
        self.cultures = ""
        self.text = ""
