from PIL import Image
import os

src = Image.open('assets/Gameboy/body.png')
os.makedirs('assets/gameboy/slices', exist_ok=True)

# Coordonnees etablies par analyse (image 355x651)
# Screen transparent: y=96-262, x=90-270
# Dpad: y=398-485, x=38-127  -> grille 3x3
# B btn: y=428-482, x=222-277
# A btn: y=408-455, x=285-337
# SELECT: y=507-560, x=95-165
# START:  y=507-560, x=175-240

def save(name, y1, y2, x1, x2):
    crop = src.crop((x1, y1, x2, y2))
    crop.save(f'assets/gameboy/slices/{name}.png')
    print(f'{name}: {x2-x1}x{y2-y1}')

# ── Lignes simples (pleine largeur) ──────────────────────────
save('gb_top',  0,   96,  0, 355)   # partie haute
save('gb_mid',  263, 398, 0, 355)   # zone logo
save('gb_gap',  486, 507, 0, 355)   # gap entre boutons et select
save('gb_bot',  561, 651, 0, 355)   # partie basse

# ── Ligne ecran ───────────────────────────────────────────────
save('gb_scr_l', 96, 263,  0,  90)   # gauche ecran
save('gb_scr_r', 96, 263, 271, 355)  # droite ecran

# ── Ligne boutons (y=398-486) ────────────────────────────────
# Cadre gauche (avant dpad)
save('gb_r4_l',  398, 486,   0,  38)
# Dpad grille 3x3: cols=[38-70, 71-95, 96-127], rows=[398-427, 428-455, 456-485]
save('gb_dp_tl', 398, 428,  38,  71)   # coin haut-gauche
save('gb_dp_up', 398, 428,  71,  96)   # HAUT (clickable)
save('gb_dp_tr', 398, 428,  96, 128)   # coin haut-droite
save('gb_dp_lf', 428, 456,  38,  71)   # GAUCHE (clickable)
save('gb_dp_ct', 428, 456,  71,  96)   # centre
save('gb_dp_rt', 428, 456,  96, 128)   # DROITE (clickable)
save('gb_dp_bl', 456, 486,  38,  71)   # coin bas-gauche
save('gb_dp_dn', 456, 486,  71,  96)   # BAS (clickable)
save('gb_dp_br', 456, 486,  96, 128)   # coin bas-droite
# Cadre entre dpad et B
save('gb_r4_m',  398, 486, 128, 222)
# B button
save('gb_btn_b', 398, 486, 222, 278)   # zone B (clickable)
# Gap entre B et A
save('gb_r4_g',  398, 486, 278, 285)
# A button
save('gb_btn_a', 398, 486, 285, 355)   # zone A (clickable)

# ── Ligne SELECT/START (y=507-561) ───────────────────────────
save('gb_r6_l',  507, 561,   0,  95)
save('gb_sel',   507, 561,  95, 166)   # SELECT (clickable)
save('gb_r6_g',  507, 561, 166, 175)
save('gb_sta',   507, 561, 175, 241)   # START (clickable)
save('gb_r6_r',  507, 561, 241, 355)
