# Contribuer un paquet d'application YunoHost

Le guide humain. La version destinée aux agents — garde-fous, catalogues de
pièges, mécanique de la CI — est [`SKILL.md`](SKILL.md) et `references/`. Les
chiffres ci-dessous viennent d'un audit des 712 dépôts `_ynh` listés dans le
catalogue [YunoHost/apps](https://github.com/YunoHost/apps) (novembre 2026).

## 1. Vous êtes le contributeur responsable

Un assistant peut écrire et relire du code de packaging ; cela ne change pas qui
en est responsable. La personne qui ouvre le commit ou la pull request assume la
justesse, la sécurité, la licence, les tests, la documentation et chaque
commentaire de relecture. La documentation officielle :

> If you still decide to use AI, we highly recommend you to be transparent and
> responsible about it, and "own" it: you must be able to understand and
> explain every piece of your code as if you wrote it yourself.
> — https://doc.yunohost.org/en/dev/packaging/

Les relecteurs refusent les paquets générés qui s'écartent du modèle : scripts
verbeux, fonctions inexistantes, arborescences non standard. Ne soumettez pas de
code que vous n'avez pas lu.

**Trailer de divulgation (obligatoire) :** tout commit dont le contenu a été
généré ou substantiellement transformé par un outil d'IA se termine par

```
Assisted-by: <agent-name>:<model-version>
```

Ne citez que les outils et analyseurs ayant réellement contribué — ni git, ni
l'éditeur, ni le compilateur. Un trailer manquant bloque l'acceptation.

## 2. Le processus

1. Changement non trivial ? Ouvrez d'abord une issue avec votre plan.
2. Partez de [`example_ynh`](https://github.com/YunoHost/example_ynh) : clonez,
   copiez, modifiez sur place. N'écrivez jamais un manifest à la main et ne
   recopiez pas l'arborescence d'un ancien paquet — le modèle et les conventions
   des helpers évoluent.
3. Travaillez dans une branche. La branche `main` d'un dépôt listé au catalogue
   est publiée automatiquement en quelques heures : ne fusionnez que ce qui a
   passé les garde-fous.
4. Déroulez le vrai cycle de vie sur une machine ou une VM jetable : installation
   → aller-retour du panneau de configuration → sauvegarde → suppression →
   restauration → mise à niveau → la même mise à niveau une seconde fois →
   changement d'URL → réinstallation. Un script que personne n'a exécuté n'est
   pas testé.
5. Lancez `package_linter` et la CI (`!testme` sur la PR). Lisez la sortie ;
   ne supposez jamais que c'est vert.
6. Ouvrez la PR et attendez-vous à des allers-retours.

## 3. Ce que contient un paquet

`manifest.toml`, `LICENSE`, `README.md`, `scripts/` à plat en v2.1 (`install
remove upgrade backup restore change_url config _common.sh`), `conf/`,
`tests.toml`, `doc/`. Modes : 755 pour les scripts du cycle de vie, 644 pour
`_common.sh`/`change_url`/`config`.

La documentation sépare un paquet relisible d'un paquet refusé :

- `doc/DESCRIPTION.md` + `DESCRIPTION_fr.md` — c'est ce que le catalogue
  affiche, pas votre README. Liste de fonctionnalités sur plusieurs lignes, sans
  remplissage du genre « application web auto-hébergée », et la paire française
  (96 % des manifests la fournissent).
- `doc/screenshots/*.png`, intégrées au README — d'abord les visuels officiels
  du projet, ensuite des captures propres.
- `doc/ADMIN.md` — médiane 9 lignes. Uniquement ce sur quoi un administrateur
  peut buter : première connexion, options risquées, ce qui ne survit pas à une
  réinstallation.
- `doc/PRE_UPGRADE.d/<version>.md` pour les notes de migration liées à une
  version.

## 4. Manifest

- `[upstream]` : `license`, `code`, plus `website`/`admindoc`/`demo` quand ils
  sont réels. `website` doit être le site du projet, jamais le dépôt de code.
- `version = "1.2.3~ynh1"` : le suffixe `~ynh` est le vôtre — incrémentez-le à
  chaque changement côté paquet.
- `helpers_version = "2.1"` dans `[integration]`, toujours. Sans cela, un paquet
  en packaging_format 2 charge silencieusement les helpers 2.0 morts.
- Questions d'installation sobres — médiane du corpus : 3. `domain`, `path`
  seulement si le sous-chemin fonctionne vraiment, `init_main_permission`
  (défaut `visitors` pour tout ce qui est public). Ne demandez que ce que
  l'installation ne peut pas décider.
- `[resources.sources]` : épinglez `url` + `sha256` (sous-tableaux par
  architecture quand la publication diffère) et déclarez `autoupdate` sur des
  tags stables — 87 % des sources épinglées le font, et c'est ce qui permet au
  bot du catalogue de proposer les montées de version.
- `integration.multi_instance` : true sauf si l'application détient de l'état
  global à la machine (ports protocolaires fixes, hooks système). Justifiez-le
  en commentaire et protégez l'installation — la plateforme n'applique pas le
  drapeau.

## 5. Scripts

- Rendez la configuration avec `ynh_config_add` (+`_fail2ban`, `_logrotate`,
  `_systemd`) depuis des modèles dans `conf/`, jamais de heredoc dans un script.
- `ynh_systemctl` pour les services ; `ynh_exec_as_app` pour exécuter en tant
  qu'utilisateur de l'app ; `ynh_safe_rm` pour les suppressions.
- Secrets : `ynh_app_setting_set_default --key=x --value=$(ynh_string_random)`,
  puis re-rendez la configuration depuis les settings à chaque passage. Ne
  régénérez jamais un secret lors d'une mise à niveau ou d'une restauration.
- Bases de données : exportez dans `backup` avec `ynh_mysql_dump_db` /
  `ynh_psql_dump_db`, restaurez avec le helper correspondant. Une application
  PostgreSQL doit aussi inclure `postgresql` dans `[resources.apt]` : la
  ressource base de données crée la base et l'utilisateur mais n'installe jamais
  le serveur.
- Vérifiez chaque appel `ynh_*` contre `/usr/share/yunohost/helpers.v2.1.d/`.
  Des helpers v2.0 morts circulent encore dans d'anciens dépôts :
  `ynh_add_config`, `ynh_secure_remove`, `ynh_use_logrotate`,
  `ynh_permission_update`.
- Commentaires : une ligne de pourquoi, ou rien. Un relecteur doit pouvoir
  suivre chaque script de haut en bas en une seule lecture.
- Rien de personnel nulle part — aucun nom, domaine privé, IP ou identifiant
  dans les fichiers, les exemples, les captures ni l'historique.

## 6. tests.toml

Gardez la ligne `#:schema`. Ajoutez des entrées `test_upgrade_from.<commit>`
issues de votre propre historique à chaque publication — c'est ce qui prouve les
montées de version pour la boutique. Renseignez `[default.args]` pour les
questions obligatoires sans défaut afin que la CI puisse installer sans
interaction, n'`exclude` que les scénarios que l'application ne peut réellement
pas servir (en le documentant), et utilisez `curl_tests` pour vérifier les pages
et le comportement de connexion.

## 7. Soumettre au catalogue

Une PR vers [YunoHost/apps](https://github.com/YunoHost/apps) ajoute l'entrée
dans `apps.toml` (état `working`, catégorie issue de `categories.toml`) et le
logo dans `logos/`. Les niveaux de qualité 0–8 sont attribués par le bot de la CI
chaque vendredi ; un niveau ≤4 masque l'application et gèle les mises à niveau
pour toutes les personnes qui l'ont installée — les scénarios de `tests.toml` ne
sont donc pas optionnels.

## 8. Liste de vérification avant la PR

- [ ] J'ai lu chaque ligne du diff et je peux la défendre comme la mienne.
- [ ] `bash -n` propre ; chaque helper `ynh_*` existe en helpers 2.1.
- [ ] Installation, sauvegarde, suppression, restauration, double mise à niveau,
      changement d'URL et réinstallation faits sur une vraie machine — pas
      seulement en CI.
- [ ] Aller-retour du panneau de configuration get → set → get vérifié sur le
      fichier rendu.
- [ ] Connexion réelle dans un navigateur et parcours d'écriture principal OK.
- [ ] `README_fr.md`, `DESCRIPTION_fr.md` et le vrai `LICENSE` amont livrés.
- [ ] `helpers_version = "2.1"`, bloc `[upstream]`, stratégie `autoupdate`
      présents.
- [ ] Suffixe `~ynh` incrémenté ; tag `v<version>-ynh<N>` existant sur le dépôt.
- [ ] Aucune donnée personnelle, historique et captures comprises.
- [ ] Trailer `Assisted-by:` sur chaque commit assisté par IA.
