# Contribuer au packaging d'applications YunoHost

Guide destiné aux humains pour contribuer aux paquets `_ynh` — vers
l'organisation [YunoHost-Apps](https://github.com/YunoHost-Apps), vers un
paquet personnel ou vers un paquet existant. Il reformule en prose simple la
doctrine de packaging, et ajoute les bonnes pratiques extraites d'un
ré-audit complet (novembre 2026) des **712 dépôts `_ynh` listés dans le
[catalogue YunoHost/apps](https://github.com/YunoHost/apps)** (`apps.toml`,
727 entrées). Les pourcentages sont mesurés sur ce corpus.

## 1. Vous êtes le contributeur responsable

Un assistant IA peut écrire, relire et refactoriser du code de packaging, mais
il ne change pas le processus : l'humain qui ouvre le commit ou la pull request
en possède tout le contenu — correction, sécurité, licence, tests, documentation
et chaque commentaire de revue. La documentation officielle est claire :

> If you still decide to use AI, we highly recommend you to be transparent and
> responsible about it, and "own" it: you must be able to understand and
> explain every piece of your code as if you wrote it yourself.
> — https://doc.yunohost.org/en/dev/packaging/

Les revieweurs rejettent les paquets « générés » qui dévient du modèle :
scripts verbeux, helpers hallucinés, architectures hors standard. Ne soumettez
jamais un code que vous n'avez pas lu personnellement.

**Règle de divulgation pour cette famille de paquets (obligatoire) :** chaque
commit dont le contenu a été généré ou substantiellement transformé par un
outil IA doit porter l'annotation :

```
Assisted-by: <nom-de-l-agent>:<version-du-modele>
```

Exemple : `Assisted-by: Hermes Agent:qwen-next`. N'indiquez que les outils IA
et analyseurs spécialisés ayant réellement contribué — pas git, les éditeurs
ni les compilateurs. L'absence de cette annotation sur un travail assisté par
IA bloque l'acceptation ici.

## 2. Le processus normal d'abord

1. Changement non trivial ? Ouvrez (ou commentez) un ticket GitHub avec votre
   plan et attendez un retour avant d'écrire du code significatif.
2. Partez de [`example_ynh`](https://github.com/YunoHost/example_ynh) — clonez,
   copiez les fichiers, éditez en place. N'écrivez jamais un manifest à la main
   ni ne copiez l'architecture d'un vieux paquet : le modèle et les helpers
   évoluent.
3. Travaillez dans une branche. La branche `main` d'un dépôt au catalogue est
   publiée automatiquement en quelques heures ; n'y fusionnez que ce qui a
   passé les tests.
4. Testez le cycle de vie réel sur une vraie machine (ou la VM LXC/Incus
   jetable recommandée par la doc) : installation → **aller-retour du panneau
   de configuration** → sauvegarde → suppression → restauration → mise à jour →
   **la même mise à jour une seconde fois** → **changement d'URL** →
   réinstallation. Un script jamais exécuté est un script non testé.
5. Lancez le linter et la CI : `package_linter` en local ; pour les dépôts du
   catalogue, le commentaire `!testme` sur la PR déclenche la CI de
   développement. Lisez la sortie, ne supposez pas le vert.
6. Ouvrez une PR, et préparez-vous à réviser pendant la revue.

## 3. Anatomie d'un paquet (ce que le corpus publie réellement)

Chaque paquet : `manifest.toml` (100 %), `LICENSE` (100 %), `README.md`
(100 %), `scripts/` (architecture v2.1 plate : `install remove upgrade backup
restore change_url config _common.sh`), `conf/` (100 %), `tests.toml`
(100 %), `doc/` (100 %). Permissions des scripts : 755 pour les scripts de
cycle de vie, 644 pour `_common.sh`/`change_url`/`config`.

La qualité de la documentation distingue le paquet acceptable du paquet rejeté :

- `doc/DESCRIPTION.md` (100 %) + `DESCRIPTION_fr.md` (81 %) — le catalogue
  affiche ceux-ci, pas votre README. 96 % des manifests accompagnent la
  description anglaise d'une traduction française ; faites pareil (liste de
  fonctionnalités multi-lignes, sans remplissage « application web
  auto-hébergée »).
- `doc/screenshots/*.png` (92 %) et intégrés au README (82 % des README les
  intègrent) — les ressources officielles en priorité, les captures ensuite.
- `doc/ADMIN.md` (44 %, médiane **9 lignes**) — uniquement ce sur quoi un.e
  admin peut trébucher : première connexion, options risquées, ce qui ne
  survit pas à une réinstallation. Court et réel bat long et générique.
- Les notes de migration versionnées vont dans `doc/PRE_UPGRADE.d/<version>.md`
  (16 %) — exécutées par la mise à jour seulement en franchissant cette
  version ; le bon endroit pour les avertissements de rupture amont.

## 4. Bonnes pratiques du manifest

- Bloc `[upstream]` : 100 % le publient — `license` (100 %), `code` (98 %),
  `website` (77 %), `admindoc` (65 %), `demo` (49 %), `fund` (18 %) si
  pertinent.
- `version = "1.2.3~ynh1"` (100 %) : le suffixe `~ynh` vous appartient —
  incrémentez-le à chaque changement du paquet, même sans changement amont.
- `helpers_version = "2.1"` dans `[integration]` (95 % le font ; les autres
  chargent silencieusement les helpers 2.0 morts). Mettez-le toujours. Les
  helpers 2.1 sont à jour sur YunoHost 12 comme sur 13 (le cœur 13 livre
  toujours `helpers.v2.1.d`).
- Questions d'installation sobres (médiane 3) : `domain`, `path` quand le
  sous-chemin fonctionne, `init_main_permission` (88 %) — et réfléchissez à la
  valeur par défaut : « visitors » pour une app publique, admins pour un outil
  privé. Ne demandez que ce que l'installation ne peut pas décider ; 53 % des
  questions ont une valeur par défaut.
- `[resources.sources]` : épinglez `url` + `sha256` (sous-tables par
  architecture `amd64.url`/`amd64.sha256`), et ajoutez `autoupdate` — **87 %
  des dépôts avec sources épinglées déclarent une stratégie de mise à jour**
  (`latest_github_release`/`latest_github_tag`, regex `asset` par
  architecture). C'est ce qui fait ouvrir les PR de bump par le bot du
  catalogue. Contraintes-la aux tags stables (`version_regex`) pour ne jamais
  publier une bêta automatiquement.
- `integration.multi_instance` : vrai par défaut (72 % du catalogue). Faux
  n'est légitime que pour un état global de la machine (ports protocole fixes,
  hooks système) — dites pourquoi en commentaire, et auto-protégez
  l'installation contre une seconde copie (la plateforme n'applique pas le
  drapeau).

## 5. Bonnes pratiques des scripts (idiomes v2.1, fréquence corpus)

- Rendez la configuration avec `ynh_config_add` (+ `_fail2ban`, `_logrotate`,
  `_systemd`) depuis des gabarits dans `conf/` — 95 % l'utilisent ; les
  fichiers de config dans `conf/`, pas de heredocs dans les scripts (seulement
  4 % en ont encore).
- `ynh_systemctl` pour gérer les services (94 %) — pas de `systemctl` brut.
- Secrets : créez-les une seule fois avec `ynh_app_setting_set_default
  --key=x --value=$(ynh_string_random)` (27 %) et régénérez la config depuis les
  settings ; ne régénérez jamais un secret en mise à jour/restauration.
- Exécutez en tant qu'utilisateur applicatif avec `ynh_exec_as_app` (39 %).
- Nettoyez avec `ynh_safe_rm` (45 %).
- Bases de données : dump dans `backup` avec `ynh_mysql_dump_db` /
  `ynh_psql_dump_db`, restauration avec le helper correspondant ; archivez
  aussi le répertoire settings/scripts (le motif du commentaire « Keep » avec
  `../settings/scripts/_common.sh`).
- **Ne copiez pas ceci depuis les anciens dépôts** — helpers v2.0 morts encore
  présents dans le corpus : `ynh_add_config` (35 dépôts), `ynh_secure_remove`
  (30), `ynh_use_logrotate` (14), `ynh_permission_update` (4). Vérifiez chaque
  appel `ynh_*` contre `/usr/share/yunohost/helpers.v2.1.d/` sur une vraie
  machine.
- Commentaires : sobres. Une ligne de capacité, ou le « pourquoi » d'un piège
  avec un lien ; pas de prose tutorielle. Un.e revieweur doit pouvoir lire
  chaque script d'une traite.
- Rien de personnel, jamais : pas de noms, domaines privés ni identifiants dans
  un fichier, un exemple ou une capture — y compris dans l'historique git.

## 6. tests.toml

100 % le publient. Bonnes pratiques du corpus : gardez la ligne `#:schema`
(73 %) ; ajoutez des entrées `test_upgrade_from.<commit>` tirées de
l'historique du dépôt à chaque publication (61 % en ont, et ce sont elles qui
prouvent les mises à jour pour la boutique) ; définissez `[default.args]` pour
les questions obligatoires sans défaut (63 %) afin que la CI installe sans
intervention ; `exclude` les scénarios légitimement impossibles (19 %) ;
`curl_tests` (36 dépôts, en croissance) permettent à la CI de vérifier les
pages et le comportement de connexion.

## 7. Soumettre au catalogue

Une PR vers [YunoHost/apps](https://github.com/YunoHost/apps) ajoute votre app
à `apps.toml` (+ le logo dans `logos/`) : état `working`, catégorie parmi
`categories.toml`. Les niveaux de qualité 0–8 sont attribués par un bot depuis
la CI chaque vendredi ; un niveau ≤4 masque l'app et gèle les mises à jour pour
chaque utilisateur, donc les scénarios de `tests.toml` ne sont pas optionnels.
Lisez attentivement le fil de soumission — les revieweurs regardent surtout les
§3–§5 de ce document.

## 8. Liste de vérification avant la PR

- [ ] J'ai lu chaque ligne du diff et je peux l'expliquer comme la mienne.
- [ ] `bash -n` propre ; chaque helper `ynh_*` existe dans les helpers 2.1.
- [ ] Installé, sauvegardé, supprimé, restauré, mis à jour deux fois,
      change_url testé, réinstallé — sur une vraie machine, pas seulement la CI.
- [ ] Aller-retour du panneau de configuration vérifié sur le fichier rendu.
- [ ] Vrai test de connexion dans un vrai navigateur pour le parcours principal.
- [ ] `README_fr.md`/`DESCRIPTION_fr.md` et le vrai texte `LICENSE` amont publiés.
- [ ] `helpers_version = "2.1"`, bloc `[upstream]`, stratégie `autoupdate` présents.
- [ ] Suffixe `~ynh` incrémenté ; tag `v<version>-ynh<N>` présent sur le dépôt distant.
- [ ] Aucune donnée personnelle, y compris historique et captures d'écran.
- [ ] Annotation `Assisted-by:` sur chaque commit assisté par IA.

*La version machine-de-la-doctrine de ces règles, avec catalogues de pièges et
mécanique des tests, se trouve dans le skill `ynh-app-packaging`.*
