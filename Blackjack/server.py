import socket
from _thread import *
import random

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server = socket.gethostbyname(socket.gethostname())
print("Server IP: " + server)
port = 5555

try:
    s.bind((server, port))
except socket.error as e:
    print(str(e))

s.listen(3)
print("Waiting for a Connection.")


def make_deck(num):
    new_deck = []
    for packs in range(num):
        for rank in range(1, 14):
            for suit in range(4):
                if suit == 0:
                    suit = "clubs"
                elif suit == 1:
                    suit = "diamonds"
                elif suit == 2:
                    suit = "hearts"
                else:
                    suit = "spades"

                new_deck += [str(rank) + "_of_" + suit]

    for write_index in range(len(new_deck)):
        read_index = random.randrange(write_index, len(new_deck))
        new_deck[read_index], new_deck[write_index] = new_deck[write_index], new_deck[read_index]

    return new_deck


def get_value(hand):
    total = 0
    num_aces = 0
    for c in hand:
        attributes = c.split("_")
        rank = int(attributes[0])
        if 10 <= rank <= 13:
            total += 10
        elif rank == 1:
            total += 11
            num_aces += 1
        else:
            total += rank
    while num_aces > 0 and total > 21:
        total -= 10
        num_aces -= 1

    return total


connections = []
current_id = 0
player_data = {}
dealer_data = {"hand": []}
num_packs = 4
deck = make_deck(num_packs)
reply = ""


def thread(client):
    global connections, current_id, num_packs, deck, player_data, dealer_data, reply

    current_id += 1
    player_data[str(current_id)] = {"id": str(current_id), "status": "not ready", "choice": "null",
                                    "response": "null", "hand": [], "value": 0}

    client.send(bytes(str(current_id), "utf-8"))

    while True:
        msg = client.recv(1024).decode("utf-8").split(":")
        if msg == ['']:
            for c in connections:
                c.close()
            current_id = 0
            player_data = {}
            dealer_data = {"hand": []}
            num_packs = 4
            deck = make_deck(num_packs)
            reply = ""
            break
        elif "status" in msg:  # ["1", "status", "ready"]
            player_data[msg[0]]["status"] = msg[2]
        elif "response" in msg:  # ["1", "response", "good,ready"]
            player_data[msg[0]]["response"] = msg[2]
        elif "choice" in msg:  # ["1", "choice", "hit", "20"]
            if player_data[msg[0]]["status"] == "playing":
                player_data[msg[0]]["choice"] = msg[2]
                player_data[msg[0]]["value"] = int(msg[3])

        if all(player_data[key]["status"] == "ready" for key in player_data):
            if all(player_data[key]["response"] == "good,ready" for key in player_data):
                client.send(bytes("wait", "utf-8"))
                for key in player_data:
                    player_data[key]["status"] = "need cards"
                    player_data[key]["response"] = "null"
                    player_data[key]["hand"] = [deck.pop()]
                dealer_data["hand"] = [deck.pop()]
                for key in player_data:
                    player_data[key]["hand"] += [deck.pop()]
                dealer_data["hand"] += [deck.pop()]
            else:
                client.send(bytes("ready", "utf-8"))

        elif all(player_data[key]["status"] == "need cards" for key in player_data):
            reply = "hands:"
            reply += "0" + "," + str(dealer_data["hand"]) + ":"
            for i, key in enumerate(player_data):
                reply += player_data[key]["id"] + "," + str(player_data[key]["hand"]) + ":"

            if all(player_data[key]["response"] == "good,hands" for key in player_data):
                reply = ""
                if get_value(dealer_data["hand"]) == 21:
                    for key in player_data:
                        player_data[key]["status"] = "game over"
                        player_data[key]["response"] = "null"
                else:
                    for key in player_data:
                        player_data[key]["status"] = "waiting"
                        player_data[key]["response"] = "null"
                    player_data["1"]["status"] = "playing"
                client.send(bytes("wait", "utf-8"))
            else:
                client.send(bytes(reply[:len(reply) - 1], "utf-8"))

        elif any(player_data[key]["choice"] == "hit" for key in player_data):
            for key in player_data:
                if player_data[key]["choice"] == "hit":
                    if player_data[key]["value"] < 21:
                        if not reply:
                            card = deck.pop()
                            player_data[key]["hand"] += [card]
                            reply = "add:" + player_data[key]["id"] + ":" + card
                        break
                    else:
                        reply = ""
                        player_data[key]["choice"] = "null"
                        break

            if all(player_data[key]["response"] == "good,add" for key in player_data):
                client.send(bytes("wait", "utf-8"))
                reply = ""
                for key in player_data:
                    player_data[key]["response"] = "null"
                    player_data[key]["choice"] = "null"
            else:
                client.send(bytes(reply, "utf-8"))

        elif any(player_data[key]["choice"] == "stand" for key in player_data):
            for i, key in enumerate(player_data):
                if player_data[key]["choice"] == "stand":
                    name = player_data[key]["id"]
                    if i == len(player_data) - 1:
                        for p in player_data:
                            player_data[p]["status"] = "dealer"
                            player_data[p]["choice"] = "null"
                        break
                    else:
                        break

            if all(player_data[key]["response"] == "good,text" for key in player_data):
                client.send(bytes("wait", "utf-8"))
                for key in player_data:
                    player_data[key]["status"] = "waiting"
                    player_data[str(int(name) + 1)]["status"] = "playing"
                    player_data[key]["choice"] = "null"
                    player_data[key]["response"] = "null"
            else:
                client.send(bytes("text:" + str(int(name) + 1), "utf-8"))

        elif all(player_data[key]["status"] == "dealer" for key in player_data):
            total = get_value(dealer_data["hand"])
            while total < 17:
                card = deck.pop()
                dealer_data["hand"] += [card]
                reply += card + ":"
                total = get_value(dealer_data["hand"])

            if all(player_data[key]["response"] == "good,add" for key in player_data):
                client.send(bytes("wait", "utf-8"))
                for key in player_data:
                    player_data[key]["status"] = "game over"
                    player_data[key]["response"] = "null"
            else:
                client.send(bytes("add:0:" + reply[:len(reply) - 1], "utf-8"))

        elif all(player_data[key]["status"] == "game over" for key in player_data):
            if all(player_data[key]["response"] == "good,over" for key in player_data):
                client.send(bytes("wait", "utf-8"))
                reply = ""
                if len(deck) < (num_packs * 52) / 2:
                    deck = make_deck(num_packs)
                for key in player_data:
                    player_data[key]["status"] = "not ready"
                    player_data[key]["choice"] = "null"
                    player_data[key]["response"] = "null"
                    player_data[key]["hand"] = []
                    player_data[key]["value"] = 0
            else:
                client.send(bytes("game over", "utf-8"))

        else:
            client.send(bytes("wait", "utf-8"))


while True:
    conn, address = s.accept()
    print("Connected to: ", address)

    if all(player_data[key]["status"] == "not ready" for key in player_data):
        start_new_thread(thread, (conn,))
        connections += [conn]
    else:
        conn.close()
