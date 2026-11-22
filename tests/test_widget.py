"""Tests sans affichage de Carto-profs (Playwright + Chromium).

Fausse API Grist, faux MapLibre et fausses réponses open data : aucune connexion réseau, données inventées.
Lancer depuis la racine du dépôt :  python3 -m pytest tests -q
"""
import functools, http.server, json, re, threading, urllib.parse
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright, expect

RACINE = Path(__file__).resolve().parent.parent
TESTS = Path(__file__).resolve().parent

LIGNES = [
    {"id": 1, "Nom": "DUVAL", "Prenom": "Claire", "mail_ouvert": "claire.duval@exemple.invalid", "Grade": "Agrégée", "Rne": "0459901A", "nbre_heure": 18},
    {"id": 2, "Nom": "LEROY", "Prenom": "Mehdi", "mail_ouvert": "m.leroy@exemple.invalid", "Grade": "Certifié", "Rne": "0459901A", "nbre_heure": 15},
    {"id": 3, "Nom": "PETIT", "Prenom": "Anaïs", "mail_ouvert": "", "Grade": "Certifiée", "Rne": "0379901B", "nbre_heure": 18},
    {"id": 4, "Nom": "ROUSSEL", "Prenom": "Jonas", "mail_ouvert": "j.roussel@exemple.invalid", "Grade": "Stagiaire", "Rne": " 0379901b ", "nbre_heure": 9},
    {"id": 5, "Nom": "BLANC", "Prenom": "Yanis", "mail_ouvert": "y.blanc@exemple.invalid", "Grade": "Certifié", "Rne": "0189901C", "nbre_heure": 18},
    {"id": 6, "Nom": "DUPONT", "Prenom": "Léa", "mail_ouvert": "l.dupont@exemple.invalid", "Grade": "Certifiée", "Rne": "0459998Q", "nbre_heure": 18},
    {"id": 7, "Nom": "VIDAL", "Prenom": "Zoé", "mail_ouvert": "z.vidal@exemple.invalid", "Grade": "Agrégée", "Rne": "37 0012", "nbre_heure": 18},
    {"id": 8, "Nom": "NOEL", "Prenom": "Hugo", "mail_ouvert": "", "Grade": "Certifié", "Rne": None, "nbre_heure": 18},
]
OPEN = {
    "0459901A": {"appellation_officielle": "Lycée du Val (fictif)", "libelle_commune": "Orléans", "latitude": 47.90, "longitude": 1.90, "nature_uai": 300, "nature_uai_libe": "LYCEE ENSEIGNT GENERAL ET TECHNOLOGIQUE", "secteur_public_prive_libe": "Public", "libelle_academie": "Orléans-Tours", "libelle_departement": "Loiret"},
    "0379901B": {"appellation_officielle": "Collège des Tilleuls (fictif)", "libelle_commune": "Tours", "latitude": 47.39, "longitude": 0.68, "nature_uai": 340, "nature_uai_libe": "COLLEGE", "secteur_public_prive_libe": "Privé sous contrat", "libelle_academie": "Orléans-Tours", "libelle_departement": "Indre-et-Loire"},
    "0189901C": {"appellation_officielle": "Lycée des Métiers (fictif)", "libelle_commune": "Bourges", "latitude": 47.08, "longitude": 2.40, "nature_uai": 320, "nature_uai_libe": "LYCEE PROFESSIONNEL", "secteur_public_prive_libe": "Public", "libelle_academie": "Orléans-Tours", "libelle_departement": "Cher"},
}
FOND = [
    {"numero_uai": "0459902B", "appellation_officielle": "Collège Fictif 2", "libelle_commune": "Gien", "latitude": 47.69, "longitude": 2.63, "nature_uai": 340, "secteur_public_prive_libe": "Public"},
    {"numero_uai": "0459903C", "appellation_officielle": "École Fictive", "libelle_commune": "Gien", "latitude": 47.70, "longitude": 2.62, "nature_uai": 151, "secteur_public_prive_libe": "Public"},
    {"numero_uai": "0459901A", "appellation_officielle": "Lycée du Val (fictif)", "libelle_commune": "Orléans", "latitude": 47.90, "longitude": 1.90, "nature_uai": 300, "secteur_public_prive_libe": "Public"},
]


@pytest.fixture(scope="session")
def serveur():
    gestion = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(RACINE))
    gestion.log_message = lambda *a: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), gestion)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


@pytest.fixture(scope="session")
def navigateur():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


class Appels:
    def __init__(self): self.geo, self.annu, self.fond, self.ban = [], [], [], []


def preparer(navigateur, serveur, taille=(1280, 800), grist=True, opendata_ko=False):
    ctx = navigateur.new_context(viewport={"width": taille[0], "height": taille[1]}, locale="fr-FR")
    page = ctx.new_page()
    appels = Appels()
    erreurs = []
    page.on("pageerror", lambda e: erreurs.append(str(e)))
    page.route("https://cdn.jsdelivr.net/**", lambda r: r.fulfill(body=(TESTS / "faux-maplibre.js").read_text() if r.request.url.endswith(".js") else "", content_type="text/javascript" if r.request.url.endswith(".js") else "text/css"))
    page.route("https://docs.getgrist.com/**", lambda r: r.fulfill(body=(TESTS / "faux-grist.js").read_text() if grist else "", content_type="text/javascript"))
    page.route("https://tiles.openfreemap.org/**", lambda r: r.abort())

    def opendata(route):
        url = route.request.url
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        if opendata_ko:
            return route.fulfill(status=503, body="indisponible")
        if "fr-en-annuaire-education" in url:
            uais = re.findall(r'"([0-9A-Z]{8})"', q.get("where", [""])[0]); appels.annu.append(uais)
            res = [{"identifiant_de_l_etablissement": "0459901A", "mail": "secretariat@lycee-val.invalid", "web": "lycee-val.invalid", "telephone": "02 00 00 00 00"}] if "0459901A" in uais else []
            return route.fulfill(json={"total_count": len(res), "results": res})
        if "/exports/json" in url:
            appels.fond.append(q.get("where", [""])[0])
            return route.fulfill(json=FOND)
        if "group_by" in url:
            return route.fulfill(json={"results": [{"libelle_academie": "Orléans-Tours"}, {"libelle_academie": "Paris"}]})
        uais = re.findall(r'"([0-9A-Z]{8})"', q.get("where", [""])[0]); appels.geo.append(uais)
        res = [{"numero_uai": u, **OPEN[u]} for u in uais if u in OPEN]
        return route.fulfill(json={"total_count": len(res), "results": res})
    page.route("https://data.education.gouv.fr/**", opendata)
    page.route("https://data.geopf.fr/**", lambda r: r.fulfill(json={"features": [{"properties": {"label": "Orléans 45000", "city": "Orléans"}, "geometry": {"coordinates": [1.909, 47.902]}}]}))
    page.goto(serveur + "/index.html")
    page.wait_for_function("window.cartoProfs")
    return page, appels, erreurs


def envoyer(page, lignes=LIGNES, options=None, acces="read table", mappings=None):
    page.evaluate("([l, o, a, m]) => window.__envoyer(l, o, a, m)", [lignes, options, acces, mappings])


def etat(page, cle):
    return page.evaluate(f"() => {{ const e = window.cartoProfs.etat(); return JSON.parse(JSON.stringify(e.{cle})); }}")


CONFIGURE = {"configure": True}


@pytest.fixture
def page_prete(navigateur, serveur):
    page, appels, erreurs = preparer(navigateur, serveur)
    page.evaluate("localStorage.setItem('carto-profs:visite', JSON.stringify({n: 9, finie: true}))")
    envoyer(page, options=CONFIGURE)
    page.wait_for_function("document.querySelectorAll('.pt').length === 3")
    yield page, appels, erreurs
    assert erreurs == [], erreurs
    page.context.close()


# ----------------------------------------------------------------------------------------------------------------
def test_liaison_grist_et_premier_demarrage(navigateur, serveur):
    page, appels, erreurs = preparer(navigateur, serveur)
    pret = page.evaluate("window.__grist.pret")
    assert pret["requiredAccess"] == "read table"
    assert pret["columns"][0]["name"] == "UAI" and all(c["optional"] for c in pret["columns"])
    envoyer(page)  # pas d'options : premier démarrage
    dialogue = page.locator("#modale")
    expect(dialogue).to_contain_text("Bienvenue dans Carto-profs")
    expect(page.locator('select[data-role="UAI"]')).to_have_value("Rne")
    expect(page.locator('select[data-role="Mail"]')).to_have_value("mail_ouvert")
    expect(page.locator('select[data-role="Prenom"]')).to_have_value("Prenom")
    expect(dialogue).to_contain_text("Accès du widget")
    expect(dialogue).to_contain_text("Lire la table sélectionnée")
    # une seule requête, seulement les UAI valides et normalisés de la table
    page.wait_for_function("document.querySelectorAll('.pt').length === 3")
    assert len(appels.geo) == 1 and sorted(appels.geo[0]) == ["0189901C", "0379901B", "0459901A", "0459998Q"]
    # UAI introuvables affichés avec une aide
    page.locator("#col-ok").click()
    page.wait_for_function("window.__grist.options && window.__grist.options.configure === true")
    page.locator("#b-introuvables").click()
    expect(dialogue).to_contain_text("0459998Q")
    expect(dialogue).to_contain_text("Format incorrect")
    expect(dialogue).to_contain_text("1 ligne n’a pas d’UAI")
    assert erreurs == []
    page.context.close()


def test_cache_navigateur(navigateur, serveur):
    page, appels, _ = preparer(navigateur, serveur)
    envoyer(page, options=CONFIGURE)
    page.wait_for_function("document.querySelectorAll('.pt').length === 3")
    page.reload(); page.wait_for_function("window.cartoProfs")
    envoyer(page, options=CONFIGURE)
    page.wait_for_function("document.querySelectorAll('.pt').length === 3")
    assert len(appels.geo) == 1, "la deuxième ouverture doit utiliser la copie du navigateur"
    page.context.close()


def test_open_data_injoignable(navigateur, serveur):
    page, _, erreurs = preparer(navigateur, serveur, opendata_ko=True)
    envoyer(page, options=CONFIGURE)
    expect(page.locator("#b-reessayer")).to_be_visible()
    expect(page.locator("#toast")).to_contain_text("ne répondent pas")
    assert erreurs == []
    page.context.close()


def test_fiche_survol_et_liens(page_prete):
    page, appels, _ = page_prete
    pt = page.locator('.pt[data-uai="0459901A"]')
    expect(pt.locator(".badge")).to_have_text("2")
    pt.hover()
    expect(page.locator(".maplibregl-popup.survol")).to_contain_text("Lycée du Val (fictif)")
    expect(page.locator(".maplibregl-popup.survol")).to_contain_text("Orléans · 2 personnes")
    pt.click()
    fiche = page.locator("#fiche")
    expect(fiche).to_contain_text("Lycée du Val (fictif)")
    expect(fiche).to_contain_text("Orléans · Lycée général et technologique · Public · 0459901A")
    expect(fiche.locator("li").first).to_contain_text("DUVAL Claire")
    expect(fiche.locator("li b").first).to_have_text("DUVAL")
    # annuaire : mail et site de l'établissement
    expect(fiche.get_by_role("link", name="Écrire à l’établissement")).to_have_attribute("href", "mailto:secretariat@lycee-val.invalid")
    expect(fiche.get_by_role("link", name="Site")).to_have_attribute("href", "https://lycee-val.invalid")
    expect(fiche.get_by_role("link", name="Itinéraire")).to_have_attribute("href", re.compile(r"openstreetmap\.org/directions"))
    fiche.get_by_role("button", name=re.compile("Voir la ligne de DUVAL")).click()
    assert page.evaluate("window.__grist.curseur") == {"rowId": 1}
    # établissement sans entrée dans l'annuaire : adresse ce.UAI@ac-…
    page.locator('.pt[data-uai="0379901B"]').click()
    expect(fiche.get_by_role("link", name="Écrire à l’établissement")).to_have_attribute("href", "mailto:ce.0379901b@ac-orleans-tours.fr")
    expect(fiche).to_contain_text("Privé")
    page.keyboard.press("Escape")
    expect(fiche).to_be_hidden()


def test_couleurs_camembert_et_legende(page_prete):
    page, _, _ = page_prete
    page.locator("#b-couleurs").click()
    m = page.locator("#modale")
    expect(m).to_contain_text("Colonnes qui font de bonnes catégories")
    m.locator('input[name="cc-col"][value="Grade"]').check()
    page.locator("#cc-suivant").click()
    expect(m).to_contain_text("Étape 2 sur 2")
    m.locator('input[type="color"][data-val="Certifié"]').evaluate("(e) => { e.value = '#112233'; e.dispatchEvent(new Event('input', {bubbles:true})); e.dispatchEvent(new Event('change', {bubbles:true})); }")
    page.locator("#cc-appliquer").click()
    page.wait_for_function("window.__grist.options && window.__grist.options.couleur.col === 'Grade'")
    sauve = page.evaluate("window.__grist.options.couleur")
    assert sauve["col"] == "Grade" and sauve["valeurs"]["Certifié"] == "#112233"
    expect(page.locator("#lib-couleur")).to_have_text("Grade")
    # deux grades dans le lycée du Val → camembert
    fond = page.locator('.pt[data-uai="0459901A"]').evaluate("e => e.style.background")
    assert "conic-gradient" in fond
    leg = page.locator("#legende")
    expect(leg.locator(".leg-item")).to_have_count(4)  # Agrégée, Certifié, Certifiée, Stagiaire (les UAI faux comptent dans la légende)
    # masquer une catégorie
    leg.locator('[data-cat="Stagiaire"]').click()
    assert len(etat(page, "visibles")) == 4
    expect(leg.locator('[data-cat="Stagiaire"]')).to_have_class(re.compile("masque"))
    # le choix actuel est en haut, coché, et se retire en un clic
    page.locator("#b-couleurs").click()
    premier = m.locator('input[name="cc-col"]').first
    expect(premier).to_have_value("Grade"); expect(premier).to_be_checked()
    expect(m.locator(".choix").first).to_contain_text("choix actuel")
    page.locator("#cc-retirer").click()
    expect(page.locator("#lib-couleur")).to_have_text("aucune")
    expect(leg.locator(".leg-item")).to_have_count(1)
    page.wait_for_function("window.__grist.options.couleur.source === 'aucune'")
    # la croix de la légende fait de même
    page.locator("#b-couleurs").click()
    m.locator('input[name="cc-col"][value="Grade"]').check(); page.locator("#cc-suivant").click(); page.locator("#cc-appliquer").click()
    expect(leg.locator(".leg-item")).to_have_count(4)
    leg.get_by_role("button", name="Retirer les couleurs").click()
    expect(leg.locator(".leg-item")).to_have_count(1)
    page.locator("#b-couleurs").click(); m.locator('input[name="cc-col"][value="Grade"]').check(); page.locator("#cc-suivant").click(); page.locator("#cc-appliquer").click()
    # couleur la plus fréquente
    page.locator("#b-couleurs").click(); page.locator("#cc-suivant").click()
    m.locator('input[name="cc-mode"][value="majoritaire"]').check(); page.locator("#cc-appliquer").click()
    fond = page.locator('.pt[data-uai="0459901A"]').evaluate("e => e.style.background")
    assert "conic" not in fond


def test_bulles_modele_et_apercu(page_prete):
    page, _, _ = page_prete
    page.locator("#b-bulles").click()
    m = page.locator("#modale")
    expect(page.locator("#bu-modele")).to_have_value("{Nom} {Prenom}")
    m.locator('input[data-colon]').nth(2).check()   # 3e colonne : la première hors modèle
    nouveau = page.locator("#bu-modele").input_value()
    assert nouveau.startswith("{Nom} {Prenom} — {")
    page.locator("#bu-modele").fill("{Nom} {Prenom} — {Grade} · {nbre_heure} h")
    expect(page.locator("#bu-apercu")).to_contain_text("— Agrégée · 18 h")
    m.locator('[data-onglet="survol"]').click()
    m.locator('input[data-survol="type"]').check()
    page.locator("#bu-enregistrer").click()
    page.wait_for_function("window.__grist.options && window.__grist.options.bulles.modele")
    assert page.evaluate("window.__grist.options.bulles.modele") == "{Nom} {Prenom} — {Grade} · {nbre_heure} h"
    page.locator('.pt[data-uai="0459901A"]').click()
    expect(page.locator("#fiche li").first).to_contain_text("DUVAL Claire — Agrégée · 18 h")


def test_fonctions_pures(page_prete):
    page, _, _ = page_prete
    r = page.evaluate("""() => {
      const c = window.cartoProfs;
      return {
        vide: c.rendreModele('{Nom} {Prenom} — {Grade} · {nbre_heure} h', {Nom: 'A', Prenom: 'B', Grade: '', nbre_heure: 12}, false),
        vide2: c.rendreModele('{Nom} {Prenom} — {Grade} · {nbre_heure} h', {Nom: 'A', Prenom: 'B', Grade: 'G', nbre_heure: null}, false),
        echappe: c.rendreModele('{Nom}', {Nom: '<b>x</b>'}),
        mailto: c.lienMailto({cci: ['a@x.fr', 'b@x.fr'], objet: 'Réunion & co'}),
        lots: c.lots(Array.from({length: 95}, (_, i) => i)).map(l => l.length),
        types: [151, 340, 300, 306, 320, 370, 999].map(c.typeEtab),
        dom: ['Orléans-Tours', 'Clermont-Ferrand', 'La Réunion', 'Aix-Marseille'].map(c.domaineAcademie),
        km: Math.round(c.distanceKm({lat: 47.9029, lon: 1.9093}, {lat: 47.3941, lon: 0.6848})),
        devine: c.deviner([{RNE_etab: '0451234A', courriel: 'a@b.fr', 'Prénom': 'x', Couleur: '#aabbcc'}], ['RNE_etab', 'courriel', 'Prénom', 'Couleur']).res
      };
    }""")
    assert r["vide"] == "A B · 12 h"
    assert r["vide2"] == "A B — G"
    assert r["echappe"] == "<b>&lt;b&gt;x&lt;/b&gt;</b>"
    assert r["mailto"] == "mailto:?bcc=a@x.fr,b@x.fr&subject=R%C3%A9union%20%26%20co"
    assert r["lots"] == [40, 40, 15]
    assert r["types"] == ["ECOLE", "CLG", "LGT", "LPO", "LP", "EREA", "AUTRE"]
    assert r["dom"] == ["ac-orleans-tours.fr", "ac-clermont.fr", "ac-reunion.fr", "ac-aix-marseille.fr"]
    assert 105 <= r["km"] <= 108
    assert r["devine"] == {"UAI": "RNE_etab", "Mail": "courriel", "Prenom": "Prénom", "Couleur": "Couleur"}


def test_selection_et_mails(page_prete):
    page, _, _ = page_prete
    page.locator('.pt[data-uai="0459901A"]').click()
    fiche = page.locator("#fiche")
    fiche.locator('#fiche-tous').check()
    barre = page.locator("#barre-selection")
    expect(barre).to_contain_text("Sélection : 2 personnes")
    expect(barre).to_contain_text("dans 1 établissement")
    expect(page.locator('.pt[data-uai="0459901A"]')).to_have_class(re.compile("choisi"))
    # sélection au rectangle : ajoute les autres établissements
    page.locator("#b-selection").click()
    expect(page.locator("#b-selection")).to_have_attribute("aria-pressed", "true")
    page.evaluate("window.cartoProfs.selectionnerZone(-5000, -5000, 5000, 5000)")
    expect(barre).to_contain_text("Sélection : 5 personnes")
    barre.get_by_role("button", name="Écrire…").click()
    m = page.locator("#modale")
    expect(m).to_contain_text("Sans adresse, donc pas dans la liste : PETIT Anaïs")
    lien = m.locator("[data-mailto]")
    expect(lien).to_have_count(1)
    href = lien.get_attribute("href")
    assert href.startswith("mailto:?bcc=") and "claire.duval@exemple.invalid" in href and "PETIT" not in href
    page.locator("#mail-objet").fill("Réunion de bassin")
    assert "subject=R%C3%A9union%20de%20bassin" in lien.get_attribute("href")
    # établissements de la sélection
    m.locator('input[name="mail-qui"][value="etabs"]').check()
    expect(m.locator(".adresses")).to_contain_text("secretariat@lycee-val.invalid")
    expect(m.locator(".adresses")).to_contain_text("ce.0189901c@ac-orleans-tours.fr")
    # personnes + établissement en copie, adresses visibles en À
    m.locator('input[name="mail-qui"][value="mixte"]').check()
    m.locator('[data-champ="a"]').click()
    href = m.locator("[data-mailto]").get_attribute("href")
    assert href.startswith("mailto:claire.duval@exemple.invalid,") and "cc=" in href and "subject=R%C3%A9union" in href
    page.keyboard.press("Escape")
    # « Écrire aux cochées » de la fiche : seulement les cochées de cet établissement
    page.locator('.pt[data-uai="0459901A"]').click()
    fiche.get_by_role("button", name=re.compile("Écrire aux 2 cochées")).click()
    expect(m).to_contain_text("Les 2 personnes de la sélection")
    page.keyboard.press("Escape")
    expect(barre).to_contain_text("Sélection : 5 personnes")
    barre.get_by_role("button", name="Vider la sélection").click()
    expect(barre).to_be_hidden()


def test_recherche_filtre_depart(page_prete):
    page, appels, _ = page_prete
    page.locator("#recherche").fill("duv")
    expect(page.locator("#resultats")).to_contain_text("DUVAL Claire")
    page.locator("#recherche").press("Enter")
    expect(page.locator("#fiche li.trouve")).to_contain_text("DUVAL")
    page.locator("#recherche").fill("tours")
    expect(page.locator("#resultats")).to_contain_text("Commune")
    # filtre
    page.locator("#b-filtre").click()
    page.locator("#fi-col").select_option("Grade")
    page.locator('#pop input[data-fv="Certifié"]').uncheck()
    assert len(etat(page, "visibles")) == 3
    expect(page.locator("#lib-filtre")).to_have_text("Filtre : Grade")
    page.locator("#fi-retirer").click()
    assert len(etat(page, "visibles")) == 5
    # point de départ
    page.locator("#b-depart").click()
    page.locator("#de-q").fill("Orléans")
    page.locator("#de-form button[type=submit]").click()
    page.locator('#de-res input[name="de-r"]').first.check()
    expect(page.locator("#lib-depart")).to_have_text("Départ : Orléans")
    page.wait_for_function("window.cartoProfs.etat().depart && window.cartoProfs.etat().depart.rayons.length === 3")
    page.locator('.pt[data-uai="0379901B"]').click()
    expect(page.locator("#fiche .dist")).to_contain_text(re.compile(r"à 1\d\d km de Orléans"))
    assert page.evaluate("JSON.parse(localStorage.getItem('carto-profs:depart')).nom") == "Orléans"


def test_tableau_de_bord_et_liste(page_prete):
    page, _, _ = page_prete
    page.locator("#b-liste").click()
    t = page.locator("#tableau")
    expect(t).to_be_visible()
    expect(t.locator("table.liste tbody tr")).to_have_count(3)
    expect(t.locator(".bloc").first).to_contain_text("Loiret")
    t.locator('[data-tri="nom"]').click()
    expect(t.locator("tbody tr").first).to_contain_text("Collège des Tilleuls")
    t.locator('input[data-tab-uai="0189901C"]').check()
    expect(page.locator("#tab-ecrire")).to_be_enabled()
    t.locator('[data-ouvrir="0379901B"]').click()
    expect(t).to_be_hidden()
    expect(page.locator("#fiche")).to_contain_text("Collège des Tilleuls")
    csv = page.evaluate("window.cartoProfs.csvEtabs()")
    lignes = csv.lstrip("﻿").split("\r\n")
    assert lignes[0].startswith("UAI;Établissement;Commune") and len(lignes) == 4
    assert any(l.startswith("0459901A;Lycée du Val (fictif);Orléans;") for l in lignes)


def test_export_png_et_impression(page_prete):
    page, _, _ = page_prete
    page.locator("#b-export").click()
    with page.expect_download() as dl:
        page.locator('[data-export="png"]').click()
    assert dl.value.suggested_filename.startswith("carto-profs-") and dl.value.suggested_filename.endswith(".png")
    page.locator("#b-export").click()
    with page.expect_download() as dl:
        page.locator('[data-export="csv-pers"]').click()
    assert dl.value.suggested_filename.endswith(".csv")


def test_theme_garde_les_points(page_prete):
    page, _, _ = page_prete
    page.locator("#b-theme").click()   # auto → clair
    page.locator("#b-theme").click()   # clair → sombre
    page.wait_for_function("window.__carte.styles.some(s => s.endsWith('/dark'))")
    page.wait_for_function("window.__carte.carte.getSource('etabs') && document.querySelectorAll('.pt').length === 3")
    assert page.evaluate("document.documentElement.dataset.theme") == "sombre"


def test_regrouper_et_fond(page_prete):
    page, appels, _ = page_prete
    assert page.evaluate("window.__carte.sources.etabs.cluster") is True
    page.locator("#c-regrouper").uncheck()
    page.wait_for_function("window.__carte.sources.etabs.cluster === false")
    page.locator("#c-fond").check()
    page.wait_for_function("window.__carte.carte.getSource('fond').data.features.length === 1")
    assert appels.fond and 'Orléans-Tours' in appels.fond[0]
    # écoles cochées : l'école du fond apparaît ; le lycée de la table n'est pas en double
    page.locator('#legende [data-type="ECOLE"]').click()
    page.wait_for_function("window.__carte.carte.getSource('fond').data.features.length === 2")
    page.wait_for_function("window.__grist.options && window.__grist.options.fond.types.includes('ECOLE')")


def test_lecteur_sans_droit_et_ecriture_coordonnees(navigateur, serveur):
    page, _, erreurs = preparer(navigateur, serveur)
    page.evaluate("localStorage.setItem('carto-profs:visite', JSON.stringify({n: 9, finie: true})); window.__grist.refuserOptions = true")
    envoyer(page, options=CONFIGURE)
    page.wait_for_function("document.querySelectorAll('.pt').length === 3")
    page.locator('#legende #c-regrouper').uncheck()
    expect(page.locator("#toast")).to_contain_text("Réglages gardés pour cette session")
    # accès complet : écrire les coordonnées
    envoyer(page, options=CONFIGURE, acces="full")
    page.locator("#b-colonnes").click()
    page.locator("#col-ecrire").click()
    page.wait_for_function("window.__grist.actions")
    actions = page.evaluate("window.__grist.actions")
    assert [a[0] for a in actions] == ["AddColumn", "AddColumn", "BulkUpdateRecord"]
    assert actions[2][2] == [1, 2, 3, 4, 5]
    assert erreurs == []
    page.context.close()


def test_mappings_du_panneau_grist(navigateur, serveur):
    page, appels, _ = preparer(navigateur, serveur)
    lignes = [{"id": 1, "Code": "0459901A", "Qui": "Mme X"}]
    envoyer(page, lignes=lignes, options=CONFIGURE, mappings={"UAI": "Code", "Nom": "Qui"})
    page.wait_for_function("document.querySelectorAll('.pt').length === 1")
    page.locator(".pt").click()
    expect(page.locator("#fiche li")).to_contain_text("Mme X")
    page.context.close()


def test_visite_guidee_reste_dans_le_cadre(navigateur, serveur):
    page, _, erreurs = preparer(navigateur, serveur, taille=(420, 520))
    envoyer(page, options=CONFIGURE)
    v = page.locator("#visite")
    expect(v).to_be_visible(timeout=4000)
    for _ in range(8):
        b = v.bounding_box()
        assert b["x"] >= 0 and b["y"] >= 0 and b["x"] + b["width"] <= 420 and b["y"] + b["height"] <= 520, b
        if page.locator("#vi-suiv").inner_text() == "Terminer":
            page.locator("#vi-suiv").click(); break
        page.locator("#vi-suiv").click()
    expect(v).to_be_hidden()
    assert page.evaluate("JSON.parse(localStorage.getItem('carto-profs:visite')).finie") is True
    # petite vue : libellés masqués, icônes seules
    assert page.locator("#b-bulles .lib").is_hidden()
    assert erreurs == []
    page.context.close()


def test_menu_aide_et_presentation(page_prete):
    page, _, _ = page_prete
    page.locator("#b-aide").click()
    expect(page.get_by_role("menuitem", name="Visite guidée")).to_be_visible()
    page.get_by_role("menuitem", name="Quoi de neuf ?").click()
    expect(page.locator("#modale")).to_contain_text("Version 1.1.0")
    page.keyboard.press("Escape")
    page.locator("#b-presentation").click()
    expect(page.locator("#barre")).to_be_hidden()
    expect(page.locator("#quitter-presentation")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.locator("#barre")).to_be_visible()


def test_demonstration_hors_grist(navigateur, serveur):
    page, _, erreurs = preparer(navigateur, serveur, grist=False)
    page.evaluate("localStorage.setItem('carto-profs:visite', JSON.stringify({n: 9, finie: true}))")
    expect(page.locator("#bandeau-demo")).to_be_visible()
    page.wait_for_function("document.querySelectorAll('.pt').length > 10")
    expect(page.locator("#lib-couleur")).to_have_text("Grade")
    assert erreurs == []
    page.context.close()


def test_points_places_par_maplibre(page_prete):
    """Régression 1.0.0 : un style « position » sur l'élément donné à MapLibre faisait dériver les points au zoom."""
    page, _, _ = page_prete
    assert page.locator(".maplibregl-marker.pt").count() == 0
    assert page.locator(".maplibregl-marker > .pt").count() == 3
    regles = page.evaluate("""() => { const d = document.createElement('div'); d.className = 'pt-ancre'; document.body.appendChild(d);
      const c = getComputedStyle(d); const r = [c.position, c.transform]; d.remove(); return r; }""")
    assert regles == ["static", "none"], regles


def test_sans_acces(navigateur, serveur):
    page, _, erreurs = preparer(navigateur, serveur)
    page.evaluate("window.__optionsSeules(null, 'none')")
    expect(page.locator("#sans-acces")).to_be_visible()
    expect(page.locator("#sans-acces")).to_contain_text("Lire la table sélectionnée")
    envoyer(page, options=CONFIGURE)
    expect(page.locator("#sans-acces")).to_be_hidden()
    assert erreurs == []
    page.context.close()
