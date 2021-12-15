
class Settlement:
    """
    Represents a settlement/region on the campaign map, including the region colour, settlement coordinates, settlement
    cultures & name.

    """
    def __init__(self, text):
        self.colour = (0, 0, 0)
        self.name = ""
        self.settlement_location = (0, 0)
        self.cultures = ""
        self.text = text

    def parse_text(self):
        """
        Parses the raw text of the Settlement entry

        :return:
        """
        return None
