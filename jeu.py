import fonctions as f


print(f"Bienvenue dans la version console du pendu !")

joueur=f.login()

print(f"On commence ?")

cheat_mode=True

f.jeu(cheat_mode,joueur)