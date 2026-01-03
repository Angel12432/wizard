from src.card import Card
from src.player import Player
import json
import numpy as np
import pandas as pd
import datetime
import math
import os

pd.set_option('display.max_columns', None)          # Verhindert, dass Spalten mit "..." abgekürzt werden
pd.set_option('display.width', 5000)                # Erlaubt eine sehr breite Darstellung im Terminal
pd.set_option('display.colheader_justify', 'center') # Zentriert die Überschriften über den Daten


rng = np.random.default_rng(seed=42)  # Zufallszahlengenerator mit Seed

colors = ["red", "green", "blue", "yellow"]

def load_player_from_config():
    # 1. Die passive Textdatei öffnen
    with open("configs/players.json", "r", encoding="utf-8") as f:
        data = json.load(f)  # Macht aus dem Text ein Dictionary

    # 2. Aus dem Text echte Python-Objekte bauen
    player_objects = []
    for s in data["player"]:
        # Hier rufen wir deine Player-Klasse auf
        new_player = Player(s["name"], 0, [], playing_style=s["playing_style"])
        player_objects.append(new_player)

    return player_objects



winner_list = []

def shuffle_cards():
    cards = []
    for color in colors:
        cards.append(Card("", 14))
        cards.append(Card("", 0))
        for value in range(13):
            cards.append(Card(color, value + 1))
    rng.shuffle(cards)
    return cards


def number_of_rounds_to_be_played(number_of_playerss):
    return 60 // number_of_playerss


def create_points_table(player_namen: list[str]) -> pd.DataFrame:
    """
    Creates an empty Pandas DataFrame for the points table.
    """
    columns = pd.MultiIndex.from_product([player_namen, ["announced_tricks", "tricks_made", "points"]],
                                         names=['player', 'category'])
    points_table = pd.DataFrame(columns=columns)
    points_table.index.name = 'round'
    # Explizite Typ-Konvertierung, um NaN zu vermeiden
    return points_table.astype('int64')

#ki
def add_points(points_table: pd.DataFrame, round_number: int,
               round_data: dict[str, list[int]]) -> pd.DataFrame:
    """
    Adds the results of a game round to the points table.
    """
    new_round = {}
    for player, daten in round_data.items():
        new_round[(player, 'announced_tricks')] = daten[0]
        new_round[(player, "tricks_made")] = daten[1]
        new_round[(player, 'points')] = daten[2]
    points_table.loc[round_number] = new_round
    return points_table


def calculate_total_points(table: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a row ‘total’ containing the sum of all ‘points’ for each player.
    """
    total_points_row = table.xs('points', level='category', axis=1).sum(axis=0)
    total_row = {}
    for player in table.columns.get_level_values('player').unique():
        total_row[(player, 'announced_tricks')] = 0
        total_row[(player, "tricks_made")] = 0
        total_row[(player, 'points')] = total_points_row[player]
        #winner_of_the_game(total_row[(player, 'points')])
    table.loc['total'] = total_row
    return table, total_points_row

def winner_of_the_game(total_row):
    winner = total_row.idxmax()
    points = total_row.max()
    winner_list.append(winner)
    return winner, points


def print_table(table: pd.DataFrame):
    #Gibt die Pandas points-table lesbar in der Konsole aus.
    print(table.to_string())


#SPIELLOGIK

def play_round(current_round, trump_color, table, number_of_rounds, playerlist):

    round_data = {}

    #cardsausgabe & Ansagen
    for player in playerlist:
        #print("-----")
        #print(f"player: {player.name}")

        #print(f"cards auf der Hand ({len(player.cards_in_hand)}): {player.cards_in_hand}")
        #print("-----")


        number_of_announced_tricks = evaluate_cards(player.cards_in_hand, trump_color, playerlist, current_round, player.playing_style)
        #print(f" -> announced_trickse tricks: {number_of_announced_tricks}")

        round_data[player.name] = [
            number_of_announced_tricks, 0, 0
        ]
        # Vorläufiges Speichern der Ansagen, damit play_trick darauf zugreifen kann
        table = add_points(table, current_round, round_data)


    trick_winner = []

    number_of_tricks_in_round = {player.name: 0 for player in playerlist}
    starting_player_index = (current_round % len(playerlist)) - 1

    for i in range(current_round):

        winner = play_trick(playerlist, starting_player_index, trump_color, current_round, table, number_of_tricks_in_round)

        trick_winner.append(winner)
        number_of_tricks_in_round[winner] += 1

        #bestimmt Index des letzten winners
        trick_winner_last_round = next(
            (player for player in playerlist if player.name == winner))
        starting_player_index = playerlist.index(trick_winner_last_round)


    for player in playerlist:
        number_of_tricks_made = number_of_made_tricks(player, trick_winner)
        number_of_announced_tricks_alt = round_data[player.name][0]
        round_data[player.name] = [number_of_announced_tricks_alt, number_of_tricks_made, 0]



    #Daten abspeichern
    for player, daten in round_data.items():
        number_of_announced_tricks = daten[0]
        number_of_tricks_made = daten[1]


        if number_of_announced_tricks == number_of_tricks_made:
            points = 20 + number_of_tricks_made * 10
        else:
            points = (abs(number_of_announced_tricks - number_of_tricks_made)) * (-10)

        round_data[player] = [number_of_announced_tricks, number_of_tricks_made, points]

    #table füllen und ausgeben

    table = add_points(table, current_round, round_data)
    table = table.fillna(0).astype(int)

    #totalsumme hinzufügen, falls es die letzte round war
    if current_round == number_of_rounds:
        table, total_points = calculate_total_points(table)
        #print("\n ENDSTAND DES SPIELS (inkl. total) 🏆")
        #print_table(table)
        winner, points = winner_of_the_game(total_points)
        #print(f" -> winner ist: {winner} mit {points} pointsn.")
    #else:
        #print("\n-----------"
        #    f"ERGEBNISSE NACH round {round}"
         #   "-----------")
        #print_table(table)

    return table


def start_game(starting_round, playerlist):

    round_number = number_of_rounds_to_be_played(len(playerlist))
    player_namen_str = [player.name for player in playerlist]
    table = create_points_table(player_namen_str)

    #print("\n===========================================")
    #print(f" STARTE WIZARD-SPIEL mit {round_number} roundn")
    #print("===========================================")

    for current_round in range(starting_round, round_number + 1):
        #print(f"\n====================== round {round} ======================")

        #shuffle cards
        cards = shuffle_cards()

        # cardsausteilen und Trumpf bestimmen
        remaining_cards = distribute_cards(cards, current_round, playerlist)
        trump_color = choose_trump(remaining_cards, current_round, playerlist)

        #print(f" Startplayer: {playerlist[round % len(playerlist) - 1]}")
        #print(f" Trumpcolor: {trump_color} | {round} cards per player")


        table = play_round(current_round, trump_color, table, round_number, playerlist)


    #print("\n Game is over.")



def distribute_cards(cards, number_of_cards, playerlist):
    for i in range(number_of_cards):
        for player in playerlist:
            top_card = cards.pop(0)
            player.cards_in_hand.append(top_card)

    return cards

def choose_trump(remaining_cards, current_round, playerlist):
    if remaining_cards:
        trump_card = remaining_cards[0]  # oberste card aufdecken
    else:
        return None

    if trump_card.color in colors:
        trump_color = trump_card.color

    elif trump_card.value == 0:
        trump_color = None

    elif trump_card.value == 14:
        frequencies = {color: 0 for color in colors}
        starting_player = playerlist[(current_round % len(playerlist)) - 1]


        for card in starting_player.cards_in_hand:
            color = card.color
            if color in colors:                                                   #ki
               frequencies[color] = frequencies.get(color,0) + 1

        #Ersatztrumpf für wizard finden --> häufigste color bei aggressiven playing_style

        if starting_player.playing_style == "aggressive":
            trump_color = max(frequencies, key=frequencies.get)  #ki
        else: trump_color = min(frequencies, key=frequencies.get)

    return trump_color


def evaluate_cards(cards, trump_color, playerlist, current_round, playing_style):
    number_of_players = len(playerlist)
    total_prob = 0

    for card in cards:
        prob = 0  # Wahrscheinlichkeit, dass diese card einen Stich macht

        if card.value == 14:
            prob = 0.95

        elif card.value == 0:
            prob = 0.05

        elif card.color == trump_color:
            # Wertigkeit im Verhältnis zu den playern
            prob = (card.value / 13) * 0.8
            if current_round < 5:
                prob += 0.1
            if card.value > 10: prob += 0.15


        else:
            # Je mehr player, desto wahrscheinlicher wird die color gestochen (Trumpf oder höher)
            basis_prob = (card.value / 13)
            # Risiko-Skalierung: Bei vielen playern sinkt die Chance einer normalen card extrem
            player_malus = 0.75 ** (number_of_players - 1)
            prob = basis_prob * player_malus

            # In hohen roundn (viele cards) werden kleine Zahlen wertlos
            if current_round > 5 and card.value < 8:
                prob *= 0.5

        total_prob += prob

    # Wir roundn mathematisch (0.5 wird aufgeroundt), statt nur abzuschneiden
    number_of_tricks = round(total_prob)

    # Sicherstellen, dass in round 1 bei einer starken card mindestens 1 geboten wird
    if current_round == 1 and total_prob > 0.4:
        return 1



    if playing_style == "aggressive":
        number_of_tricks = math.floor(total_prob + 0.7)
    else:
        # Normales roundn
        number_of_tricks = round(total_prob)

    return min(number_of_tricks, len(cards))


def play_trick(playerlist, starting_player_index, trump_color, current_round, table, number_of_tricks_in_round):
    trick_cards = {}
    operating_color = ""
    current_winning_card = None
    winner = None

    for i in range(len(playerlist)):

        active_player = playerlist[(starting_player_index + i) % len(playerlist)]
        #print(active_player)

        # 1. Daten aus der table holen
        planned_tricks = table.loc[current_round, (active_player.name, 'announced_tricks')]
        # "tricks_made" tracken wir hier besser lokal oder über eine Variable,
        # da die table erst am Ende der round befüllt wird
        current_made_tricks = number_of_tricks_in_round[active_player.name]

        wants_trick = current_made_tricks < planned_tricks

        # finde alle erlaubten cards
        possible_cards = permitted_cards_for_move(active_player.cards_in_hand, operating_color)


        played_card = (choose_smart_card
                         (possible_cards, current_winning_card, trick_cards, operating_color, trump_color, playerlist, wants_trick, playing_style=active_player.playing_style))

        if operating_color == "" and played_card.color != "":
            operating_color = played_card.color

        # Jetzt prüfen, ob die neue card (vielleicht die erste Farbcard nach einem Narren) führt
        if current_winning_card is None or is_stronger(played_card, current_winning_card, operating_color, trump_color):
            current_winning_card = played_card
            winner = active_player.name


        active_player.cards_in_hand.remove(played_card)
        trick_cards[active_player.name] = played_card



    #print(f"Der Stich: {trick_cards}")
    #winner, card = winner_of_the_trick(trick_cards, operating_color, trump_color)
    #print(f"winner des tricks ist: {winner} mit {card}")

    return winner


def choose_smart_card(cards, highest_trick_card, trick_cards, operating_color, trump_color, playerlist, wants_trick=True, playing_style="normal"):

    winner_cards = []
    loser_cards = []

    for card in cards:
        # Wenn noch keine card liegt, gewinnt man (außer mit Narr)
        if highest_trick_card is None:
            if card.value > 0:
                winner_cards.append(card)
            else:
                loser_cards.append(card)
        # Ansonsten: Prüfung gegen die aktuell beste card
        elif is_stronger(card, highest_trick_card, operating_color, trump_color):
            winner_cards.append(card)
        else:
            loser_cards.append(card)

    # 2. Strategie anwenden
    if wants_trick:
        if winner_cards:
            if playing_style == "aggressive":
                if not trick_cards:
                    trump_cards = [card for card in winner_cards if card.color == trump_color]
                    if trump_cards:
                        return max(trump_cards, key=lambda card: card.value)
                # AGGRESSIV: Nimm die HÖCHSTE card, die gewinnt (den "Sack zumachen")
                return max(winner_cards, key=lambda card: card.value)
            else:
                # NORMAL: Nimm die kleinste card, die gerade so sticht (Sparen)
                return min(winner_cards, key=lambda card: card.value)
        else:
            # Kann nicht gewinnen -> kleinste card wegwerfen
            normal_color_cards = [card for card in loser_cards if card.color != trump_color and card.value not in [0,14]]
            if normal_color_cards:
                return min(normal_color_cards, key=lambda card: card.value)
            return min(cards, key=lambda card: card.value)

    else:
        if loser_cards:
            wizards = [card for card in loser_cards if card.value == 14]
            if wizards:
                return wizards[0]

            trump_cards = [card for card in loser_cards if card.color == trump_color]

            if trump_cards:
                # Werfe den höchsten Trumpf ab, der gerade NICHT sticht
                return max(trump_cards, key=lambda card: card.value)

            # Wenn kein Trumpf zum Abwerfen da ist, nimm die höchste normale card
            return max(loser_cards, key=lambda card: card.value)
        else:
            # Muss leider gewinnen -> kleinste card opfern
            number_of_cards_in_trick = len(trick_cards)
            still_players_left = number_of_cards_in_trick < (len(playerlist)-1)
            if still_players_left:
                return min(cards, key=lambda card: card.value)
            else:
                return max(cards, key=lambda card: card.value)


def is_stronger(new_card, best_card_so_far, operating_color, trump_color):
    # 1. wizard-Regel: Der erste wizard im Stich gewinnt immer.
    # Wenn die card, die bereits führt, ein wizard (14) ist,
    # kann keine nachfolgende card sie mehr schlagen.
    if best_card_so_far.value == 14:
        return False

    # Wenn die neue card ein wizard ist (und die beste bisher keiner war), führt sie jetzt.
    if new_card.value == 14:
        return True

    # 2. Narren-Regel: Ein Narr (0) kann niemals eine card schlagen, die bereits führt.
    if new_card.value == 0:
        return False

    # 3. Trumpf-Logik:
    # Neue card ist Trumpf, die beste bisherige aber nicht.
    if new_card.color == trump_color and best_card_so_far.color != trump_color:
        return True
    # Beide sind Trumpf -> der höhere Wert gewinnt.
    if new_card.color == trump_color and best_card_so_far.color == trump_color:
        return new_card.value > best_card_so_far.value

    # 4. Bediencolorn-Logik:
    # Neue card bedient die color, die beste bisherige ist aber weder Trumpf noch Bediencolor.
    if new_card.color == operating_color and best_card_so_far.color != operating_color:
        # (Da wir oben Trumpf schon geprüft haben, wissen wir hier: best_card_so_far ist kein Trumpf)
        return True
    # Beide haben die Bediencolor -> der höhere Wert gewinnt.
    if new_card.color == operating_color and best_card_so_far.color == operating_color:
        return new_card.value > best_card_so_far.value

    # 5. Alle anderen Fälle:
    # Wenn die neue card eine falsche color hat (Abwurf) oder kleiner ist, gewinnt sie nicht.
    return False






def permitted_cards_for_move(cards, operating_color):
    if not operating_color:
        return cards

    operating_color_cards = [card for card in cards if card.color == operating_color]
    if not operating_color_cards:
        return cards

    permitted_cards = [card for card in cards if card.color == operating_color or card.color == ""]
    return permitted_cards



def number_of_made_tricks(player, trick_winner):
    number_of_tricks_made = trick_winner.count(player.name)
    return number_of_tricks_made




def play_games(number_of_games, playerlist):
    for i in range (number_of_games):
        start_game(1, playerlist)


def winning_probabilities(winner_liste, number_of_games, playerlist):
    probabilities = {player.name: winner_liste.count(player.name) / number_of_games for player in playerlist}

    df = pd.DataFrame(probabilities, index=["winningchance"])

    #Für die Anzeige in der Konsole in Prozent umwandeln
    df_percent= df.map(lambda x: f"{x * 100:.1f}%")

    #Speichern (df_percentnutzen)
    export_with_metadata(df_percent, "last_simulation", seed=42)

    return df_percent



def export_with_metadata(df, dateiname, seed=42):
    """Speichert einen DataFrame mit Metadaten-Header in den reports-Ordner."""

    os.makedirs("reports", exist_ok=True) #erstelltOrdner reports falls er fehlt

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    #Header-Zeilen zusammen mit # am Anfang
    header = [
        f"# Projekt: Wizard Simulation",
        f"# Erstellungsdatum: {timestamp}",
        f"# Verwendeter Seed: {seed}",
        f"# Status: Finales Ergebnis",
        "#"
    ]

    path = f"reports/{dateiname}.csv"

    #Erst den Header schreiben, dann den DataFrame anhängen
    with open(path, 'w', encoding='utf-8') as f:
        f.write("\n".join(header) + "\n")
        df.to_csv(f, index=True)

    #print(f"Ergebnisse erfolgreich gespeichert unter: {path}")