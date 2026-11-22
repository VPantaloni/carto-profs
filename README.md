# Carto-profs — carte des personnes d’une table Grist

**Adresse du widget à coller dans Grist :**

```
https://widget.forge.apps.education.fr/carto-profs/
```

Carto-profs transforme une table Grist de personnes (professeur·es, formateur·trices, membres d’un groupe de travail…)
en **carte interactive** : un point par établissement, retrouvé tout seul dans les données ouvertes de l’Éducation
nationale à partir de l’**UAI** (RNE). Couleurs au choix, fiches, recherche, filtres, distances, envoi de mails,
tableau de bord et exports. Tutoriel pour les usager·es : [`tuto.html`](https://widget.forge.apps.education.fr/carto-profs/tuto.html)
(aussi ouvert par le **(?)** en haut à droite du widget). Page d’accueil avec démonstration intégrée :
[widget.forge.apps.education.fr/carto-profs](https://widget.forge.apps.education.fr/carto-profs/) ouverte dans un onglet
(hors de Grist, l’adresse du widget mène à `accueil.html` ; la démonstration seule : `index.html?demo`).

## Démarrage rapide

1. Ouvrez le document Grist et la page qui contient la table des personnes.
2. **Nouveau → Ajouter une vue à la page** ; type de vue **Personnalisé** ; données : **votre table**.
3. Panneau de droite : **URL personnalisée**, collez l’adresse ci-dessus.
4. Accès : **Lire la table sélectionnée** (c’est tout ce qu’il faut).
5. Au premier lancement, vérifiez les colonnes reconnues, puis **Voir la carte**. Une visite guidée présente les boutons.
6. Facultatif : ajoutez une vue **Fiche** de la même table avec **Sélectionner par → Carto-profs** ; le bouton
   « voir la ligne dans Grist » de chaque personne y affichera sa ligne.

Pour essayer : importez [`exemple/carto-profs-exemple.csv`](exemple/carto-profs-exemple.csv) dans Grist
(**Nouveau → Importer depuis un fichier**), données entièrement inventées.

## Colonnes attendues

Les noms sont libres : le widget les **devine** (noms et valeurs). On peut aussi les choisir dans le panneau de droite
de Grist (rubrique des colonnes du widget) ou avec le bouton **Colonnes** du widget.

| Rôle | Exemples de noms | Type Grist conseillé | Obligatoire |
|---|---|---|---|
| UAI de l’établissement (7 chiffres + 1 lettre) | `Rne`, `UAI` | Texte | **oui** |
| Nom, Prénom | `Nom`, `Prenom` | Texte | conseillé |
| Mail | `mail_ouvert`, `Mail` | Texte | pour écrire |
| Libellé (texte libre) | `Libelle` | Texte | non |
| Groupe (couleurs) | `Groupe`, ou n’importe quelle colonne choisie dans « Colorier selon… » | Texte, Choix | non |
| Couleur imposée | `Couleur` (`#2563eb`) | Texte | non |
| Établissement, commune (secours si l’UAI est inconnu de l’open data) | `EtabNom`, `EtabVille` | Texte | non |
| Latitude, longitude (passent avant l’open data) | `Latitude`, `Longitude` | Numérique | non |

Toutes les autres colonnes restent utilisables pour les couleurs, les bulles et les filtres. Le widget fonctionne avec
la table `Profs_maths_26_27` telle quelle (`Rne`, `Nom`, `Prenom`, `mail_ouvert`, `Grade`…).

## Droits

- **Widget** : « Lire la table sélectionnée » suffit pour la carte. Il ne crée ni n’écrit rien.
- **Groupes** : demandent l’**accès complet au document**. Le widget crée deux tables, `Carto_groupes` (`Nom`,
  `Couleur`, `Description`) et `Carto_membres` (`Groupe` → Carto_groupes, `Nom`, `Prenom`, `Mail`, `UAI`, `Source`).
  Les membres sont retrouvés dans la table des personnes par mail, puis nom + prénom + UAI, puis nom + prénom :
  les groupes suivent quand la table est remplacée l’année suivante. Un membre absent de la table mais avec un UAI
  est placé quand même (« hors table »).
- **Option « Écrire les coordonnées »** (bouton Colonnes) : ajoute et remplit `Latitude` / `Longitude` ; demande
  l’**accès complet au document**. À n’accorder que si on s’en sert.
- **Réglages** (couleurs, bulles, fond d’établissements…) : gardés dans les **options du widget**, donc dans le
  document et partagés par tous ses lecteurs. Seules les personnes qui peuvent modifier le document les enregistrent.
- **Lecteurs** : le widget marche pour une personne qui n’a que la lecture du document.

<details>
<summary>Confidentialité : ce qui sort du navigateur</summary>

- Les **UAI** de la table, par paquets de 50, vers
  [data.education.gouv.fr](https://data.education.gouv.fr) (jeux « Adresse et géolocalisation des établissements
  d’enseignement du premier et second degrés » et « Annuaire de l’éducation »).
- L’adresse tapée pour le **point de départ**, vers le service d’adresses de l’IGN (`data.geopf.fr`).
- Les tuiles du fond de carte (OpenFreeMap).
- **Jamais** les noms, mails ou autres colonnes. Les mails s’ouvrent dans la messagerie de l’usager·e : le widget
  n’envoie rien.
- Copies gardées dans le navigateur (`localStorage`, préfixe `carto-profs:`) : positions et annuaire des
  établissements (30 jours, 7 jours pour un UAI inconnu), fond d’établissements de l’académie, point de départ,
  thème, visite guidée.
</details>

<details>
<summary>Fonctionnalités</summary>

- Carte MapLibre GL 4.7.1, fonds OpenFreeMap `positron` / `dark` (thème automatique ou manuel).
- Un point par établissement, badge du nombre de personnes, **camembert** si plusieurs couleurs (ou couleur la plus
  fréquente), regroupement des points proches.
- **Colorier selon…** : colonnes candidates repérées avec aperçu, palettes (dont daltonisme), couleur par valeur,
  dégradé pour les nombres et les dates, couleur lue dans une colonne `#rrggbb`. Légende cliquable avec compteurs.
- **Bulles** : survol (commune, type, nombre) ; fiche avec modèle de ligne `{Nom} {Prenom} — {Grade}`, colonnes à
  cocher et ordonner, aperçu en direct ; liens mail, site, itinéraire OpenStreetMap, « voir la ligne dans Grist ».
- **Fond d’établissements** d’une académie, filtrable (écoles, CLG, LYC, EREA, autres ; public, privé).
- **Recherche** (personne, établissement, UAI, commune), **filtre** par colonne, **point de départ** avec cercles
  10 / 20 / 50 km et distances.
- **Sélection** (fiches, rectangle sur la carte, liste) et **mails** : sélection, personnes affichées, établissements,
  personnes + établissement en copie ; Cci par défaut ; lots de 40 adresses ; copie des adresses.
- **Groupes** : nom, couleur, description ; membres ajoutés depuis la fiche, la sélection, ou une liste collée / un CSV
  (mails, « NOM Prénom », tableau avec titres) avec rapprochement automatique et validation des doutes (homonymes, noms
  approchés) ; membres hors table placés par leur UAI ; coloriage par groupes (camembert si plusieurs, « Hors groupe »
  en gris, masquable) ; CSV par groupe.
- **Zones de remplacement** (UAI `037002ZK` : 6 chiffres + `Z` + lettre) : une bulle par zone, rangée autour des
  départements avec un trait de rappel vers sa zone (côté donné par son nom : OUEST, EST, NORD, SUD, lu dans la colonne
  établissement ; sinon le bord le plus proche) ; case « Groupes de ZR » ; **contours des
  départements** ; bouton **Voir tous les points** sous la boussole.
- **Tableau de bord** (département, type, catégorie), **liste** accessible au clavier, exports **PNG**, **CSV**,
  impression **A4**, **mode présentation**.
- UAI introuvables et lignes sans UAI signalés avec une aide ; démonstration hors de Grist.
</details>

<details>
<summary>Développement et tests</summary>

Un seul fichier `index.html` (HTML + CSS + JS, module ES), sans étape de construction. Icônes Lucide intégrées.
`departements.geojson` (300 Ko) : contours simplifiés des départements, publiés à côté du widget et lus par lui.

Tests sans affichage (Playwright + Chromium) avec une fausse API Grist, un faux MapLibre et de fausses réponses
open data, données inventées :

```sh
pip install pytest playwright && python -m playwright install chromium
python -m pytest tests -q
```

`exemple/carto-profs-exemple.csv` et la démonstration intégrée (`const DEMO` dans `index.html`) contiennent les mêmes
données fictives (UAI inventés, avec leurs coordonnées).
</details>

<details>
<summary>Publication (GitHub → Forge)</summary>

- Dépôt de travail : GitHub `VPantaloni/carto-profs`. À chaque poussée sur `main`, l’action
  `.github/workflows/forge.yml` recopie le dépôt vers `forge.apps.education.fr/widget/carto-profs`.
- Le jeton d’accès de la Forge va dans **Settings → Secrets and variables → Actions → `FORGE_TOKEN`** du dépôt GitHub
  (jeton de projet ou personnel, portée `write_repository`). Jamais dans le code.
- Sur la Forge, `.gitlab-ci.yml` publie `index.html`, `tuto.html`, `departements.geojson` et `exemple/` avec GitLab Pages.
- `.github/workflows/tests.yml` lance les tests à chaque poussée.
</details>

<details>
<summary>Crédits et licence</summary>

Licence **EUPL 1.2** (voir `LICENSE`). Fond de carte © OpenFreeMap, © contributeurs OpenStreetMap ;
contours des départements : [france-geojson](https://github.com/gregoiredavid/france-geojson) (G. David) d’après
Admin Express © IGN, Licence ouverte, simplifiés ; données
© ministère de l’Éducation nationale, Licence Ouverte (data.education.gouv.fr) ; géocodage IGN Géoplateforme ;
icônes [Lucide](https://lucide.dev) (ISC) ; [MapLibre GL JS](https://maplibre.org) (BSD-3-Clause).
</details>
