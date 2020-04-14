import pygame
import sys
import socket

WIDTH = 1024
HEIGHT = 950
FPS = 60

BLACK = (0, 0, 0)
BROWN = (60, 33, 33)
WHITE = (255, 255, 255)
OFF_POS = (-300, -300)
IP_INFO_POS = (WIDTH / 2, 125)
IP_INPUT_POS = (WIDTH / 2, 175)
CARD_ARRAY_POS = (WIDTH / 2, 450)
TABLE_POS = (WIDTH / 2, HEIGHT / 2 - 46)
MONEY_POS = (90, 90)
HEADER_POS = (WIDTH / 2, 35)
READY_POS = (WIDTH / 2, 875)
PLUS_POS = (710, 830)
MINUS_POS = (710, 920)
BET_POS = (710, 875)
DECK_POS = (828, 300)
PLAYER1_POS = (196, 603)
PLAYER2_POS = (512, 603)
PLAYER3_POS = (827, 603)
DEALER_POS = (513, 177)
HIT_POS = (115, 875)
STAND_POS = (WIDTH / 2, 875)
DOUBLE_POS = (WIDTH - 115, 875)
HAND_VALUE_POS = (WIDTH / 2, 725)
WIN_POS = (WIDTH / 2, 300)
MINIMUM_BET = 5
STARTING_CASH = 100

pygame.init()
pygame.font.init()
pygame.mixer.init()
clock = pygame.time.Clock()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
large_font = pygame.font.SysFont("./assets/Roboto.ttf", 50)
small_font = pygame.font.SysFont("./assets/Roboto.ttf", 25)
pygame.display.set_caption("blackjack")


class Network:
    def __init__(self, ip):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = ip
        self.port = 5555
        self.address = (self.host, self.port)
        self.id = self.connect()

    def connect(self):
        self.client.settimeout(1)
        self.client.connect(self.address)

        return self.client.recv(1024).decode()

    def send(self, data):
        try:
            self.client.send(str.encode(data))
            reply = self.client.recv(1024).decode()
            return reply
        except socket.error as e:
            return str(e)


class Sprite(pygame.sprite.Sprite):
    def __init__(self, image, pos, resize):
        super().__init__()
        self.image_path = image
        self.image = pygame.image.load(image)
        self.image = pygame.transform.rotozoom(self.image, 0, resize)

        self.rect = self.image.get_rect()
        self.rect.center = pos

    def change_image(self, image, resize):
        self.image = pygame.image.load(image)
        self.image = pygame.transform.rotozoom(self.image, 0, resize)

    def change_pos(self, game, name, new_pos, pos, card_num=0):
        if name == "0":
            dy = new_pos[1] + (card_num * 21) - pos[1]
            dx = new_pos[0] - pos[0]
        elif name == "1":
            dx = new_pos[0] + (card_num * 21) - pos[0]
            dy = new_pos[1] - pos[1]
        elif name == "2":
            dy = new_pos[1] - (card_num * 21) - pos[1]
            dx = new_pos[0] - pos[0]
        elif name == "3":
            dx = new_pos[0] - (card_num * 21) - pos[0]
            dy = new_pos[1] - pos[1]
        else:
            dy = new_pos[1] - pos[1]
            dx = new_pos[0] - pos[0]

        for i in range(0, 1001, 25):
            self.rect.center = pos[0] + int(dx * (i / 1000)), pos[1] + int(dy * (i / 1000))
            game.processing()


class Card(Sprite):
    def __init__(self, rank, suit, image_path, pos, resize):
        super().__init__(image_path, pos, resize)
        self.rank = rank
        self.suit = suit

    def move_card(self, game, name, card_num):
        self.rect.center = DECK_POS
        if name == "0":
            self.change_pos(game, name, DEALER_POS, DECK_POS, card_num)
        elif name == "1":
            self.change_pos(game, name, PLAYER1_POS, DECK_POS, card_num)
        elif name == "2":
            self.change_pos(game, name, PLAYER2_POS, DECK_POS, card_num)
        elif name == "3":
            self.change_pos(game, name, PLAYER3_POS, DECK_POS, card_num)


class Text(pygame.sprite.Sprite):
    def __init__(self, text, pos, color, font):
        super().__init__()
        self.text = text
        self.color = color
        self.font = font
        self.image = font.render(self.text, True, color)

        self.rect = self.image.get_rect()
        self.rect.center = pos

    def change_text(self, text, pos):
        self.text = text
        self.image = self.font.render(text, True, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = pos


class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.multiplier = 1

    def get_value(self):
        total = 0
        num_aces = 0
        for card in self.hand:
            if 10 <= card.rank <= 13:
                total += 10
            elif card.rank == 1:
                total += 11
                num_aces += 1
            else:
                total += card.rank
        while num_aces > 0 and total > 21:
            total -= 10
            num_aces -= 1

        return total


class Game:
    def __init__(self):
        self.net = None
        self.msg = ""

        self.sprites = pygame.sprite.Group()
        self.cards = pygame.sprite.Group()
        self.players = []
        self.player = None
        self.money = STARTING_CASH
        self.bet = 5

        self.card_array = Sprite("./assets/card array.png", CARD_ARRAY_POS, 0.2)
        self.ip_info = Text("Input the server's ip address:", IP_INFO_POS, BLACK, large_font)
        self.ip_input = Text("IP: ", IP_INPUT_POS, WHITE, large_font)
        self.table = Sprite("./assets/table.png", OFF_POS, 0.5)
        self.header = Text("BLACKJACK", HEADER_POS, WHITE, large_font)
        self.money_ui = Text(str(self.money), OFF_POS, WHITE, large_font)
        self.ready_button = Sprite("./assets/not ready.png", OFF_POS, 0.16)
        self.plus_button = Sprite("./assets/plus.png", OFF_POS, 0.09)
        self.bet_ui = Text("", OFF_POS, WHITE, small_font)
        self.minus_button = Sprite("./assets/minus.png", OFF_POS, 0.09)
        self.hit_button = Sprite("./assets/hit.png", OFF_POS, 0.16)
        self.stand_button = Sprite("./assets/stand.png", OFF_POS, 0.16)
        self.double_button = Sprite("./assets/double.png", OFF_POS, 0.16)
        self.hand_value_ui = Text("", OFF_POS, WHITE, large_font)
        self.chip = Sprite("./assets/casino chip.png", OFF_POS, 0.35)
        self.sprites.add(self.card_array, self.ip_info, self.ip_input, self.table, self.header, self.chip,
                         self.money_ui, self.ready_button, self.plus_button, self.bet_ui, self.minus_button,
                         self.hit_button, self.stand_button, self.double_button, self.hand_value_ui)

    def start_game(self):
        self.ready_button.rect.center = OFF_POS
        self.plus_button.rect.center = OFF_POS
        self.minus_button.rect.center = OFF_POS
        self.bet_ui.rect.center = OFF_POS

        for p in self.players[1:]:  # ["0", "1", "2", "3"] -> ["1", "2", "3"]
            p.hand[0].move_card(self, p.name, 0)

        self.players[0].hand[0].change_image("./assets/cards/back_of_card.png", 0.15)
        self.players[0].hand[0].move_card(self, "0", 0)

        for p in self.players[1:]:  # ["0", "1", "2", "3"] -> ["1", "2", "3"]
            p.hand[1].move_card(self, p.name, 1)

        self.players[0].hand[1].move_card(self, "0", 1)

        self.hit_button.rect.center = HIT_POS
        self.stand_button.rect.center = STAND_POS
        self.double_button.rect.center = DOUBLE_POS
        self.hand_value_ui.change_text("Your Hand: " + str(self.player.get_value()), HAND_VALUE_POS)

    def processing(self):
        # Update
        self.sprites.update()
        self.cards.update()
        if self.net:
            self.msg = self.net.send("nothing")

        # Draw
        screen.fill(BROWN)
        self.sprites.draw(screen)
        self.cards.draw(screen)

        # Flip
        pygame.display.flip()

    def run(self):
        running = True
        while running:

            clock.tick(30)

            for event in pygame.event.get():

                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    keys = pygame.key.get_pressed()

                    if self.plus_button.rect.collidepoint(x, y):
                        if self.bet < self.money:
                            if keys[304]:
                                self.bet += 5
                            elif keys[306]:
                                self.bet += 20
                            else:
                                self.bet += 1

                            if self.bet > self.money:
                                self.bet = self.money
                            self.bet_ui.change_text(str(self.bet), BET_POS)

                    if self.minus_button.rect.collidepoint(x, y):
                        if self.bet > MINIMUM_BET:
                            if keys[304]:
                                self.bet -= 5
                            elif keys[306]:
                                self.bet -= 20
                            else:
                                self.bet -= 1

                            if self.bet < MINIMUM_BET:
                                self.bet = MINIMUM_BET
                            self.bet_ui.change_text(str(self.bet), BET_POS)

                    if self.ready_button.rect.collidepoint(x, y):
                        self.ready_button.change_image("./assets/ready.png", 0.16)
                        self.net.send(self.net.id + ":status:ready")

                    if self.hit_button.rect.collidepoint(x, y):
                        self.net.send(self.net.id + ":choice:hit:" + str(self.player.get_value()))

                    if self.stand_button.rect.collidepoint(x, y):
                        self.net.send(self.net.id + ":choice:stand:" + str(self.player.get_value()))

                    if self.double_button.rect.collidepoint(x, y) and self.money >= self.bet * 2 and len(self.player.hand) == 2:
                        self.net.send(self.net.id + ":choice:hit:" + str(self.player.get_value()))
                        self.player.multiplier = 2

                if event.type == pygame.KEYDOWN:

                    if event.key == 27:
                        running = False

                    if event.key == 46 or 48 <= event.key <= 57 and len(self.ip_input.text) < 20:
                        text = self.ip_input.text + pygame.key.name(event.key)
                        self.ip_input.change_text(text, IP_INPUT_POS)

                    if event.key == 8 and len(self.ip_input.text) > 4:
                        text = self.ip_input.text[:-1]
                        self.ip_input.change_text(text, IP_INPUT_POS)

                    if event.key == 13 and self.table.rect.center == OFF_POS:
                        try:
                            self.net = Network(self.ip_input.text[4:])
                        except (ConnectionRefusedError, OSError):
                            self.ip_input.change_text("IP: ", IP_INPUT_POS)
                        if self.net:
                            if self.net.id != "":
                                self.card_array.rect.center = OFF_POS
                                self.table.rect.center = TABLE_POS
                                self.chip.rect.center = MONEY_POS
                                self.money_ui.change_text(str(self.money), MONEY_POS)
                                self.plus_button.rect.center = PLUS_POS
                                self.bet_ui.change_text(str(self.bet), BET_POS)
                                self.minus_button.rect.center = MINUS_POS
                                self.header.change_text("You are Player " + self.net.id + ": Not Playing", HEADER_POS)
                                self.ready_button.rect.center = READY_POS

                if event.type == pygame.QUIT:
                    running = False

            self.processing()

            if "closed" in self.msg:
                pygame.quit()
                sys.exit()

            if "ready" in self.msg:  # "ready"
                self.net.send(self.net.id + ":response:good,ready")
                for card in self.cards:
                    card.kill()
                if self.net.id == "1":
                    text = "You are Player " + self.net.id + ": Your Turn"
                else:
                    text = "You are Player " + self.net.id + ": Player 1's Turn"
                self.header.change_text(text, HEADER_POS)

            if "hands:" in self.msg:  # hands:0,[]:1,[]:2,[]:3,[]
                self.net.send(self.net.id + ":response:good,hands")
                hands = self.msg.split(":")[1:]  # "hands:0,[]:1,[]:2,[]:3,[]" -> ["0,[]", "1,[]", "2,[]", "3,[]"]
                if self.players != len(hands):
                    for i in range(len(hands)):
                        self.players += [Player(str(i))]
                    self.player = self.players[int(self.net.id)]

                for i, p in enumerate(hands):
                    cards = eval(p[2:])  # "0,["whatever"]" -> ["whatever"]
                    hand = []
                    for c in cards:
                        attributes = c.split("_")  # "10_of_diamonds" -> ["10", "of", "diamonds"]
                        rank = attributes[0]
                        suit = attributes[2]
                        image_path = "./assets/cards/" + rank + "_of_" + suit + ".png"
                        card = Card(int(rank), suit, image_path, (-100, -100), 0.15)
                        hand += [card]
                        self.cards.add(card)
                        self.players[i].hand = hand

                self.start_game()

                if self.player.get_value() == 21:
                    self.player.multiplier = 1.5
                    self.hand_value_ui.change_text("Your Hand: Blackjack", HAND_VALUE_POS)
                    self.net.send(self.net.id + ":choice:stand:" + str(self.player.get_value()))

            if "add:" in self.msg:  # add:0:10_of_spades:9_of_hearts
                self.net.send(self.net.id + ":response:good,add")
                msg = self.msg.split(":")[1:]  # add:0:10_of_spades:9_of_hearts -> ["0", "10_of_spades", "9_of_hearts"]
                name = msg[0]
                cards = msg[1:]  # ["0", "10_of_spades", "9_of_hearts"] -> ["10_of_spades", "9_of_hearts"]
                if name == "0":
                    first_card = self.players[0].hand[0]
                    first_card.change_image(first_card.image_path, 0.15)

                if cards != [""]:
                    for c in cards:
                        attributes = c.split("_")  # "10_of_diamonds" -> ["10", "of", "diamonds"]
                        rank = attributes[0]
                        suit = attributes[2]
                        image_path = "./assets/cards/" + rank + "_of_" + suit + ".png"
                        card = Card(int(rank), suit, image_path, (-100, -100), 0.15)
                        self.cards.add(card)
                        self.players[int(name)].hand += [card]
                        card.move_card(self, name, len(self.players[int(name)].hand) - 1)

                    if name == self.net.id:
                        if self.player.get_value() >= 21 or self.player.multiplier == 2:
                            self.net.send(self.net.id + ":choice:stand:" + str(self.player.get_value()))
                        if self.player.get_value() > 21:
                            self.hand_value_ui.change_text("Your Hand: Busted", HAND_VALUE_POS)
                        else:
                            self.hand_value_ui.change_text("Your Hand: " + str(self.player.get_value()), HAND_VALUE_POS)

            if "text:" in self.msg:  # "text:3"
                self.net.send(self.net.id + ":response:good,text")
                text = self.msg.split(":")  # "text:3" -> ["text", "3"]
                if self.net.id == text[1]:
                    text = "You are Player " + self.net.id + ": Your Turn"
                else:
                    text = "You are Player " + self.net.id + ": Player " + text[1] + "'s Turn"
                self.header.change_text(text, HEADER_POS)

            if self.msg == "game over":
                if self.players:
                    self.net.send(self.net.id + ":response:good,over")

                    first_card = self.players[0].hand[0]
                    first_card.change_image(first_card.image_path, 0.15)

                    player_value = self.player.get_value()
                    dealer_value = self.players[0].get_value()
                    if dealer_value == 21:
                        outcome = "Loss"
                    elif player_value > 21:
                        outcome = "Loss"
                    elif dealer_value > 21:
                        outcome = "Win"
                    elif player_value == 21:
                        outcome = "Win"
                    elif player_value < dealer_value:
                        outcome = "Loss"
                    elif player_value > dealer_value:
                        outcome = "Win"
                    else:
                        outcome = "Push"

                    if outcome == "Win":
                        self.money += self.bet * self.player.multiplier
                        chip = Sprite("./assets/casino chip.png", WIN_POS, 0.35)
                        self.sprites.add(chip)
                        chip.change_pos(self, "-1", MONEY_POS, WIN_POS)
                        chip.kill()
                    elif outcome == "Loss":
                        self.money -= self.bet * self.player.multiplier
                        chip = Sprite("./assets/casino chip.png", MONEY_POS, 0.35)
                        self.sprites.add(chip)
                        chip.change_pos(self, "-1", WIN_POS, MONEY_POS)
                        chip.kill()
                    elif outcome == "Push":
                        chip = Sprite("./assets/casino chip.png", WIN_POS, 0.35)
                        self.sprites.add(chip)
                        chip.change_pos(self, "-1", READY_POS, WIN_POS)
                        chip.kill()

                    if self.bet > self.money:
                        self.bet = MINIMUM_BET
                    if self.money < MINIMUM_BET:
                        self.money = 100

                    self.players = []
                    self.header.change_text("You are Player " + self.net.id + ": Not Playing", HEADER_POS)
                    self.money_ui.change_text(str(self.money), MONEY_POS)
                    self.plus_button.rect.center = PLUS_POS
                    self.bet_ui.change_text(str(self.bet), BET_POS)
                    self.minus_button.rect.center = MINUS_POS
                    self.hit_button.rect.center = OFF_POS
                    self.stand_button.rect.center = OFF_POS
                    self.double_button.rect.center = OFF_POS
                    self.hand_value_ui.change_text("Your Hand: " + outcome, HAND_VALUE_POS)
                    self.ready_button.change_image("./assets/not ready.png", 0.16)
                    self.ready_button.rect.center = READY_POS

        pygame.quit()
        sys.exit()


Game().run()
