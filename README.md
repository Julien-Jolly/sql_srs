app de révision sql /

20/10/24 début ajouts perso:
- choix du thème
- ajout énoncé
- ajout difficulté
- système d'authentification avec envoi d'un code pour reinit du mdp
- divers ajustements graphiques avec 2 tables par ligne, solution masquée, enlever les indices des tables etc.
- ajout de filtres dynamiques
- fichier users et data csv sur gdrive (ça lag un peu au démarrage mais c'est gratuit et cela permet notamment la persistance des users)

Je pense ajouter encore pas mal de choses :
- stocker l'ensemble du code permettant la création des df des exercices et trouver comment les lancer automatiquement et les stocker sur la db (c'est sur la develop, ça tourne en local mais c'est ko sur st cloud)
- un système de score avec 2 modes, un avec questions au hasard sans incentive et l'autre mode story ou tu commences easy pour finir hardcore avec classement)
- exercices pandas
- commenter le code et le readme
- une fois le souci de stockage des df réglé ajout de questions par l'utilisateur
- un bon refacto, certaines fonctions présentes dans auth.py devraient etre dans app.py, un peu de réoganisation à faire dans le code.
