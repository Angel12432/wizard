from src.wizard_logic import load_player_from_config, play_games, winner_list, winning_probabilities, load_player_from_config

if __name__ == "__main__":

    full_playerlist = load_player_from_config()

    try:
        n = int(input("How many players should participate? (3-6) ?: "))
        if not (3 <= n <= 6):
            print("Invalid number of players. Continue with 3 players.")
            n = 3
    except ValueError:
        print("Input was not a number. Continue with 3 players.")
        n = 3

    print(f"Wizard simulation is starting with {n} players.")
    print("Testo_Torsten is playing aggressive")

    playerlist = full_playerlist[:n]

    number_of_games = 500

    play_games(number_of_games, playerlist)

    stats = winning_probabilities(winner_list, number_of_games, playerlist)
    print("\n Simulation is done.")
    print(100*"-")
    print(stats)