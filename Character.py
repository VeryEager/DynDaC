
class Character:
    """
    Represents a character on the campaign map, including position, army composition and character name.

    """
    def __init__(self, text):
        self.position = (0, 0)
        self.name = ""
        self.text = text

    def parse_text(self):
        """
        Parses the raw text of the Character entry

        :return:
        """
        return None
