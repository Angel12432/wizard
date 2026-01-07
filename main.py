from src.wizard_logic import load_player_from_config, play_games, winner_list, winning_probabilities

if __name__ == "__main__":
    """
    Entry point for the Wizard game simulation.
    Handles user input, initializes players, and executes the simulation.
    """

    # Load all available player profiles from the JSON configuration
    full_playerlist = load_player_from_config()

    try:
        #Request user input for the number of participants
        n = int(input("How many players should participate? (3-6) ?: "))

        # Validate player count (Wizard is officially for 3-6 players)
        if not (3 <= n <= 6):
            print("Invalid number of players. Continue with 3 players.")
            n = 3
    except ValueError:
        # Fallback if the user enters text instead of a number
        print("Input was not a number. Continue with 3 players.")
        n = 3

    print(f"Wizard simulation is starting with {n} players.")
    print("Testo_Torsten is playing aggressive")

    # Select the first n players from the loaded config list.
    playerlist = full_playerlist[:n]

    #Set the scale of the simulation
    number_of_games = 1000

    # Start the simulation loop
    play_games(number_of_games, playerlist)

    # Calculate statistics based on the winner_list populated during play_games
    stats = winning_probabilities(winner_list, number_of_games, playerlist)

    # Final output of results
    print("\n Simulation is done.")
    print(100*"-")
    print(stats)