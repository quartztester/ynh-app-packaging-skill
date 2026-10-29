# flarum_ynh 2.0 (YunoHost-Apps, 2026-10)

- Flarum 2 support needs the Flarum-2 fork of the LDAP login extension (`yippy/flarum-ext-auth-ldap`, core ^2.0; its settings model is ONE JSON key `<extid>.domains` — array of domain objects, seed via SQL, MEMBER group id 3) replacing `tituspijean/flarum-ext-auth-ldap` (^1.0, dead). Composer 1→2 mechanics: traps-build-and-appcode.md.
- config.php `driver` MUST be `mariadb` on YunoHost: Flarum 2 gates JSON SQL dialect by driver name and MariaDB rejects MySQL's `CAST(? AS JSON)` (500 db_error on posting). Set it in the install template AND rewrite it in the kept config.php on upgrade.
- change_url must `flarum cache:clear` after rewriting config.php (compiled state caches base URL; brief not_found window otherwise), and remove must `ynh_del_swap` (ynh_add_swap leaves /swap_$app + fstab + .swap unit).
