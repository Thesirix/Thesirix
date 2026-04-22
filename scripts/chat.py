BUBBLE_HEIGHT = 42
PADDING_BOTTOM = 15

# y positions des messages dans le template (ordre : msg1, msg2, msg3, msg4)
MSG_Y_POSITIONS = [20, 70, 120, 170]


def calculer_largeur(texte):
    return int(len(texte) * 7.5) + 35


def generer_chat():
    with open('template.svg', 'r', encoding='utf-8') as fichier:
        modele = fichier.read()

    msg1 = "Hi! What kind of magic do you do?"
    msg2 = "I'm a software developer in Marseille! ☀️"
    msg3 = "What's your favorite spell?"
    msg4 = "Saying 'It works on my Windows machine' 🪄"

    w1 = calculer_largeur(msg1)
    w2 = calculer_largeur(msg2)
    w3 = calculer_largeur(msg3)
    w4 = calculer_largeur(msg4)

    x2 = 590 - w2
    x4 = 590 - w4

    x_typing2 = w2 - 65
    x_typing4 = w4 - 65

    svg_height = MSG_Y_POSITIONS[-1] + BUBBLE_HEIGHT + PADDING_BOTTOM

    svg_final = modele.replace('{MSG_1}', msg1)
    svg_final = svg_final.replace('{MSG_2}', msg2)
    svg_final = svg_final.replace('{MSG_3}', msg3)
    svg_final = svg_final.replace('{MSG_4}', msg4)

    svg_final = svg_final.replace('{W_MSG_1}', str(w1))
    svg_final = svg_final.replace('{W_MSG_2}', str(w2))
    svg_final = svg_final.replace('{W_MSG_3}', str(w3))
    svg_final = svg_final.replace('{W_MSG_4}', str(w4))

    svg_final = svg_final.replace('{X_MSG_2}', str(x2))
    svg_final = svg_final.replace('{X_MSG_4}', str(x4))

    svg_final = svg_final.replace('{X_TYPING_2}', str(x_typing2))
    svg_final = svg_final.replace('{X_TYPING_4}', str(x_typing4))

    svg_final = svg_final.replace('{SVG_HEIGHT}', str(svg_height))

    with open('chat.svg', 'w', encoding='utf-8') as fichier:
        fichier.write(svg_final)

    print("done !")

if __name__ == "__main__":
    generer_chat()