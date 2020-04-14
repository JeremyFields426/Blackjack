import os
import pyperclip

names = "pyinstaller -n Blackjack "
for file in os.listdir("./assets/cards"):
    names += "--add-data "
    names += '"' + "./assets/cards/" + file + ";" + "./assets/cards/" + file + '"'
    names += " "
for file in os.listdir("./assets"):
    if ".png" in file:
        names += "--add-data "
        names += '"' + "./assets/" + file + ";" + "./assets/" + file + '"'
        names += " "

names += "-F client.py"

print(names)
pyperclip.copy(names)
