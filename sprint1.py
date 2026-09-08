class Player:
    def __init__(self, id, username, score):
        self.id = id
        self.username = username
        self.score = score

players = []

player = Player(1, "Alice", 100)
players.append(player)

player = Player(2, "Bob", 150)
players.append(player)

def add_player():
    username = input("Username")
    player_id = len(players) + 1
    player = Player(player_id, username, 0)
    players.append(player)
    print("Speler toegevoegd.")


def show_players():
    for player in players:
        print(player.id, player.username, player.score)

def find_player():
    username = input("Welke speler zoek je?")

    for player in players:
        if player.username.lower() == username.lower():
            print(
                f"ID: {player.id} | "
                f"Username: {player.username} |"
                f" Score: {player.score}"
            )
            return

        print("Speler niet gevonden.")

def update_score():
    username = input("Username: ")

    for player in players:
        if player.username.lower() == username.lower():
            new_score = int(input("Nieuwe score: "))
            player.score = new_score

            print("Score aangepast.")
            return

    print("Speler niet gevonden.")

def update_score():
    username = input("Username: ")

    for player in players:
        if player.username.lower() == username.lower():

            try:
                new_score = int(input("Nieuwe score: "))
            except ValueError:
                print("De score moet een getal zijn.")
                return

            player.score = new_score

            print("Score aangepast.")
            return

    print("Speler niet gevonden.")


def add_score():
    username = input("Username: ")

    for player in players:
        if player.username.lower() == username.lower():

            try:
                points = int(input("Aantal punten: "))
            except ValueError:
                print("Voer een geldig getal in.")
                return

            player.score += points

            print(f"Nieuwe score: {player.score}")
            return

    print("Speler niet gevonden.")


sorted_player = sorted(
    players,
    key=lambda player: player.score,
    reverse=True
)

def show_leaderboard():
    sorted_players = sorted(
        players,
        key=lambda player: player.score,
        reverse=True
    )

    print("\n--- LEADERBOARD ---")

    for position, player in enumerate(sorted_players, start=1):
        print(
            f"{position}. {player.username} - {player.score}"
        )


while True:

    print("\n--- PLAYER MENU ---")
    print("1. Speler toevoegen")
    print("2. Alle spelers bekijken")
    print("3. Speler zoeken")
    print("4. Score wijzigen")
    print("5. Score toevoegen")
    print("6. Leaderboard bekijken")
    print("0. Afsluiten")

    choice = input("Maak een keuze: ")

    if choice == "1":
        add_player()

    elif choice == "2":
        show_players()

    elif choice == "3":
        find_player()

    elif choice == "4":
        update_score()

    elif choice == "5":
        add_score()

    elif choice == "6":
        show_leaderboard()

    elif choice == "0":
        print("Programma afgesloten.")
        break

    else:
        print("Ongeldige keuze.")