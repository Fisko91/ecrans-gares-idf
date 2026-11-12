# Écrans gares IDF – mise à jour automatique des horaires

Chaque nuit (vers 3h30), GitHub télécharge le GTFS d'Île-de-France Mobilités, extrait les trains
(RER, Transilien, TER) pour les 21 jours suivants et publie :

- `https://<ton-compte>.github.io/<nom-du-dépôt>/` : l'écran (version web / iPhone)
- `https://<ton-compte>.github.io/<nom-du-dépôt>/horaires-ferres.json.gz` : les horaires, lus automatiquement par l'écran

## Mise en place (une seule fois, ~10 min)

1. Crée un compte sur github.com.
2. « New repository » : nom `ecrans-gares-idf`, **Public**, puis « Create repository ».
3. « uploading an existing file » : glisse `extraire-horaires.py`, `LISEZ-MOI.md` et le dossier `site`, puis « Commit changes ».
4. Le fichier de la tâche planifiée : « Add file > Create new file », nom exact
   `.github/workflows/horaires.yml`, colle le contenu du fichier `horaires.yml` fourni, puis « Commit changes ».
   (Sur Mac, le dossier `.github` est masqué dans le Finder : c'est pour ça qu'on le crée à la main.)
5. « Settings > Pages » : dans « Source », choisis **GitHub Actions**.
6. « Actions » > « Horaires théoriques IDFM » > « Run workflow ». Attends la coche verte (~5 min).

Ensuite tout est automatique.

- iPhone : ouvre `https://<ton-compte>.github.io/ecrans-gares-idf/` dans Safari > Partager > « Sur l'écran d'accueil ».
  Les horaires s'y mettent à jour seuls.
- Android : ⚙ Réglages > « Mise à jour automatique » : colle
  `https://<ton-compte>.github.io/ecrans-gares-idf/horaires-ferres.json.gz` > « Vérifier maintenant ».

## Bon à savoir

- Aucune clé PRIM n'est stockée sur GitHub : le dépôt ne contient que des horaires publics.
- GitHub met en pause les tâches planifiées d'un dépôt inactif depuis 60 jours ; la tâche fait
  un petit enregistrement le 1er de chaque mois pour l'éviter. Si elle s'arrête quand même :
  onglet « Actions » > « Enable workflow ».
- Pour changer l'écran (nouvelle version), remplace `site/index.html`.
- Source des horaires : Île-de-France Mobilités, licence ODbL.
