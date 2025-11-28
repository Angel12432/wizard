class Card:
    def __init__(self, color, value):
        self.color = color
        self.value = value

    def __str__(self):
        if self.value == 14:
            return "Zauberer"
        if self.value == 0:
            return "Narr"
        return f'{self.color} {self.value}'
