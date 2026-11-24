![Odoo PO Translator](docs/brand/logo.svg)

[English](README.md) · [Français](README.fr.md)

# Odoo PO Translator

Un environnement de travail de bureau et une interface en ligne de commande pour examiner et traduire les fichiers gettext \`.po\` utilisés par Odoo.

**Projet :** [GitHub](https://github.com/K11E3R/odoo_translator) · **Site :** [Site du projet](https://k11e3r.github.io/odoo_translator/) · **Licence :** MIT

> **Périmètre actuel :** traduction IA en ligne via le SDK officiel Google Gen AI \`google-genai\`, ainsi qu'un petit glossaire hors ligne déterministe pour des termes et expressions Odoo fréquents en anglais/français et anglais/espagnol. Le mode hors ligne n'est pas un moteur généraliste de traduction automatique.

## Fonctionnalités

- Import, fusion et export de fichiers gettext/Odoo PO.
- Interface de bureau CustomTkinter : recherche, filtres, pagination, édition, annulation/rétablissement et export.
- Traduction Gemini avec le SDK Python Google Gen AI actuellement pris en charge.
- Assistance par glossaire hors ligne pour des expressions et termes Odoo courants (EN↔FR et EN↔ES).
- Détection locale par heuristiques intégrées ; Lingua peut être installé en option pour améliorer la couverture.
- Vérification des placeholders et du balisage avant d'accepter une traduction IA.
- Cache thread-safe avec clés hachées et écritures atomiques.
- Interface CLI : simulation, remplacement du fichier ou dossier de sortie.
- Conservation du contexte gettext et des entrées au pluriel lors des fusions.

## Prérequis

- Python 3.11 ou version ultérieure.
- Tk pour l'interface graphique (Debian/Ubuntu : \`sudo apt install python3-tk\`).
- Une clé API Gemini uniquement pour la traduction en ligne.

## Installation

\`\`\`bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
\`\`\`

Sous Windows PowerShell, activez l'environnement avec \`.venv\\Scripts\\Activate.ps1\`.

### Détection de langue optionnelle

Pour une détection locale plus riche, installez Lingua séparément :

```bash
pip install -e ".[language-detection]"
```

Sans cette option, l'application utilise ses heuristiques locales et ne télécharge pas de modèle de langue.

## Application de bureau

\`\`\`bash
python app.py
\`\`\`

Saisissez une clé Gemini dans l'application pour utiliser la traduction en ligne. La clé saisie dans l'interface reste en mémoire pendant la session : elle n'est pas enregistrée dans le dépôt.

Pour utiliser le glossaire local sans clé API, activez **Offline glossary mode** dans la barre latérale. Ce mode n'effectue aucun appel réseau. Les textes absents du glossaire restent inchangés.

## Ligne de commande

\`\`\`bash
# Glossaire hors ligne anglais -> français
po-translator translate module.po --source en --target fr --offline

# Français -> anglais, remplacement atomique du fichier source
po-translator translate module.fr.po --source fr --target en --offline --in-place

# Traduction Gemini en ligne
GEMINI_API_KEY="votre-clé" po-translator translate module.po --source en --target fr

# Simulation sans écriture
po-translator translate module.po --source en --target fr --offline --dry-run
\`\`\`

Variables d'environnement :

- \`GEMINI_API_KEY\` (ou \`GOOGLE_API_KEY\`) : clé Gemini Developer API.
- \`PO_TRANSLATOR_GEMINI_MODEL\` : nom du modèle ; valeur par défaut \`gemini-3.5-flash-lite\`.
- \`PO_TRANSLATOR_OFFLINE_MODE=1\` : démarre l'application en mode glossaire hors ligne.
- \`PO_TRANSLATOR_RATE_LIMIT\` : délai minimum entre appels API, par défaut \`0.2\` seconde.

## Contrôles de traduction

Avant d'accepter une réponse en ligne, le moteur vérifie que les placeholders, balises HTML/XML et retours à la ligne sont conservés, y compris les placeholders répétés. Une réponse invalide est réessayée puis rejetée ; le texte source reste inchangé.

Le cache se trouve dans \`~/.po_translator/translation_cache.json\`. Les écritures sont atomiques et les clés de cache sont des empreintes SHA-256.

Le glossaire hors ligne est volontairement limité. Il ne prétend pas traduire un texte libre quelconque. Utilisez Gemini ou faites relire les textes par un traducteur professionnel pour les phrases complexes et les langues non couvertes.

## Fichiers PO

Les entrées gettext sont identifiées par \`msgctxt\`, \`msgid\` et \`msgid_plural\`. La fusion conserve donc les entrées contextuelles et les formes plurielles distinctes. L'export utilise polib et préserve les métadonnées PO importées.

Relisez toujours les fichiers traduits avant leur déploiement dans une base Odoo de production et conservez une copie de l'original.

## Développement et tests

\`\`\`bash
python -m pytest
\`\`\`

Les tests ne nécessitent pas de clé Gemini. Les appels Gemini doivent être testés séparément avec une clé dédiée et un petit fichier PO de test.

## Sécurité

- Stockez les clés API dans des variables d'environnement ou un gestionnaire de secrets.
- Ne publiez jamais \`.config\`, \`.env\`, des clés API ou des fichiers PO clients.
- En mode en ligne, les chaînes soumises sont envoyées à l'API Gemini de Google. Vérifiez les règles de traitement des données de votre organisation avant d'envoyer des informations confidentielles.
- Le glossaire hors ligne n'effectue aucun appel à une API de traduction. La détection de langue est locale et ne télécharge pas de modèle lors de l'import.

Consultez [SECURITY.md](SECURITY.md).

## Limites

- Le mode hors ligne est un glossaire/recueil d'expressions, pas un modèle neuronal.
- La détection de langue reste indicative et peut être incertaine pour les mots isolés et les cognats.
- Une traduction IA peut être incorrecte sur le plan du sens. Relisez les résultats.
- L'application graphique nécessite un environnement de bureau ; utilisez la CLI pour les traitements sans interface graphique.

## Contribution

Les rapports de bogues et les pull requests sont les bienvenus. Ajoutez un petit fichier PO reproductible, le résultat attendu, le résultat observé et la version de Python. N'ajoutez aucune donnée client ni aucun secret.
