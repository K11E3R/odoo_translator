![Odoo PO Translator](docs/brand/logo.svg)

[English](README.md) · [Français](README.fr.md)

# Odoo PO Translator

**Pour les développeurs et intégrateurs Odoo :** localisez les fichiers `.po` de vos modules avec la traduction assistée par Gemini, la fusion gettext qui respecte les contextes et les pluriels, et une interface de bureau ou une CLI permettant de relire les résultats.

L'objectif est de réduire les tâches répétitives de localisation tout en gardant les traductions vérifiables avant leur déploiement dans une base Odoo de production. La traduction en ligne utilise Google Gemini ; le glossaire hors ligne intégré ne couvre que certains termes Odoo en anglais/français et anglais/espagnol.

**Projet :** [GitHub](https://github.com/K11E3R/odoo_translator) · **Site :** [Site du projet](https://k11e3r.github.io/odoo_translator/) · **Licence :** MIT · [Guide de marque](docs/BRAND_GUIDE.md)

## Aperçu de l'application

![Interface de bureau Odoo PO Translator avec le tableau des traductions et les commandes](docs/screenshots/main-interface.png)

*L'espace de travail pour importer, relire, modifier et exporter les fichiers gettext d'Odoo.*

## Fonctionnalités

- Import, fusion et export de fichiers gettext/Odoo PO.
- Interface de bureau CustomTkinter : recherche, filtres, pagination, édition, annulation/rétablissement et export.
- Traduction Gemini via le SDK Python Google Gen AI actuellement pris en charge.
- Glossaire hors ligne limité à certains termes et expressions Odoo (EN↔FR et EN↔ES) ; les textes non reconnus restent inchangés.
- Détection locale par heuristiques intégrées ; Lingua peut être installé en option pour améliorer la couverture.
- Vérification des placeholders et du balisage avant d'accepter une traduction IA.
- Cache de traduction avec clés hachées, accès thread-safe au sein d'un processus et écritures atomiques.
- CLI avec simulation, remplacement atomique du fichier source et dossier de sortie.
- Fusion gettext qui distingue les contextes et les entrées au pluriel.

## Prérequis

- Python 3.11 ou version ultérieure.
- Git, pour installer directement depuis ce dépôt GitHub.
- Tk pour l'interface graphique (Debian/Ubuntu : `sudo apt install python3-tk`).
- Une clé API Gemini uniquement pour la traduction en ligne ; le glossaire hors ligne n'en a pas besoin.

## Installation

Installez l'application directement depuis GitHub en une commande :

```bash
python -m pip install "git+https://github.com/K11E3R/odoo_translator.git"
```

Puis lancez l'application de bureau :

```bash
po-translator gui
```

La même installation fournit la commande `po-translator` pour la CLI. Pour une installation isolée, utilisez plutôt `pipx install "git+https://github.com/K11E3R/odoo_translator.git"`. Sur Debian/Ubuntu, installez d'abord `python3-tk` si Tk est absent.

### Détection de langue optionnelle

Pour une détection locale plus riche, installez l'extra facultatif depuis une copie du dépôt :

```bash
python -m pip install -e ".[language-detection]"
```

Sans cette option, l'application utilise ses heuristiques locales et ne télécharge pas de modèle de langue.

## Application de bureau

Lancez l'interface installée avec `po-translator gui`. Saisissez une clé Gemini dans l'application pour utiliser la traduction en ligne. La clé saisie dans l'interface reste en mémoire pendant la session : elle n'est pas enregistrée dans le dépôt.

Pour utiliser le glossaire local sans clé API, activez **Offline glossary mode** dans la barre latérale. Ce mode n'effectue aucun appel réseau. Il ne traduit que les expressions et termes présents dans le glossaire ; les textes inconnus restent inchangés et sont signalés comme non reconnus.

## Ligne de commande

Glossaire hors ligne, de l'anglais vers le français :

```bash
po-translator translate module.po --source en --target fr --offline
```

Français vers anglais, avec remplacement atomique du fichier source :

```bash
po-translator translate module.fr.po --source fr --target en --offline --in-place
```

Traduction Gemini en ligne :

```bash
GEMINI_API_KEY="votre-clé" po-translator translate module.po --source en --target fr
```

Choisir un dossier de sortie ou vérifier sans écrire de fichier :

```bash
po-translator translate module.po --source en --target fr --output-dir build
po-translator translate module.po --source en --target fr --offline --dry-run
```

Variables d'environnement :

- `GEMINI_API_KEY` (ou `GOOGLE_API_KEY`) : clé Gemini Developer API.
- `PO_TRANSLATOR_GEMINI_MODEL` : nom du modèle ; valeur par défaut `gemini-3.5-flash-lite`.
- `PO_TRANSLATOR_OFFLINE_MODE=1` : démarre l'application en mode glossaire hors ligne.
- `PO_TRANSLATOR_RATE_LIMIT` : délai minimum entre appels API, par défaut `0.2` seconde.

## Contrôles de traduction

Avant d'accepter une réponse en ligne, le moteur vérifie que les placeholders, balises HTML/XML et retours à la ligne sont conservés, y compris les placeholders répétés. Une réponse invalide est réessayée puis rejetée ; le texte source reste inchangé.

Le cache se trouve dans `~/.po_translator/translation_cache.json`. Les écritures sont atomiques et les clés de cache sont des empreintes SHA-256.

Le glossaire hors ligne est volontairement limité. Il ne prétend pas traduire un texte libre quelconque. Utilisez Gemini ou faites relire les textes par un traducteur professionnel pour les phrases complexes et les langues non couvertes.

## Fichiers PO

Les entrées gettext sont identifiées par `msgctxt`, `msgid` et `msgid_plural`. La fusion conserve donc les entrées contextuelles et les formes plurielles distinctes. L'export utilise polib et préserve les métadonnées PO importées.

Relisez toujours les fichiers traduits avant leur déploiement dans une base Odoo de production et conservez une copie de l'original.

## Développement et tests

Pour les contributeurs travaillant depuis une copie du dépôt :

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

Les tests ne nécessitent pas de clé Gemini. Les appels Gemini doivent être testés séparément avec une clé dédiée et un petit fichier PO de test.

## Sécurité

- Stockez les clés API dans des variables d'environnement ou un gestionnaire de secrets.
- Ne publiez jamais `.config`, `.env`, des clés API ou des fichiers PO clients.
- En mode en ligne, les chaînes soumises sont envoyées à l'API Gemini de Google. Les requêtes utilisent `store=False` afin de ne pas conserver l'historique des interactions côté serveur ; les traitements et règles de données habituels de Google restent applicables. Vérifiez les règles de votre organisation avant d'envoyer des informations confidentielles.
- Le glossaire hors ligne n'effectue aucun appel à une API de traduction. La détection de langue est locale et ne télécharge pas de modèle lors de l'import.

Consultez [SECURITY.md](SECURITY.md).

## Limites

- Le mode hors ligne est un glossaire/recueil d'expressions, pas un modèle neuronal.
- La détection de langue reste indicative et peut être incertaine pour les mots isolés et les cognats.
- Une traduction IA peut être incorrecte sur le plan du sens. Relisez les résultats.
- L'application graphique nécessite un environnement de bureau ; utilisez la CLI pour les traitements sans interface graphique.

## Contribution

Les rapports de bogues et les pull requests sont les bienvenus. Ajoutez un petit fichier PO reproductible, le résultat attendu, le résultat observé et la version de Python. N'ajoutez aucune donnée client ni aucun secret.
