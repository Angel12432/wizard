class Player:
    def __init__(self, name, points, cards_in_hand, playing_style="normal"):
        self.name = name
        self.points = points
        self.cards_in_hand = cards_in_hand
        self.playing_style = playing_style


    def __str__(self):
        return f'{self.name}'
    def __repr__(self):
        return f'{self.name}'
