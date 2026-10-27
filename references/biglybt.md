# BiglyBT — domain notes for a future biglybt_ynh / arr+i2p integration

Feasibility facts verified 2026-10 by direct fetch (tarball + GitHub API + live endpoints); unverified items are marked.

## Distribution
- Linux tarball: `https://files.biglybt.com/installer/BiglyBT_unix.tar.gz` — rolling-latest URL (no per-version assets: pin/sha256 in a manifest needs a mirrored GitHub Release asset, per the packaging hosting rule in SKILL.md).
- ~50 MB, ARCH-INDEPENDENT single tree `biglybt/`: `BiglyBT.jar` + `biglybt` launcher + bundled `plugins/` only. No bundled JRE → needs a Java runtime; GPL/GPLv3 files in-tree.
- Bundled plugins (tarball): aercm, azlocprov, azmsgsync, azrating, azupdater, azupnpav, azutp, dorkboxupdater, migratetorrentapp, mlDHT, mlab. NOT bundled — fetched from the plugin site at runtime (a package must vendor the jars or pre-seed the plugin dir): xmwebui, azneti2phelper, azexec (command runner), rssfeed.
- Headless run: the standard `-Djava.awt.headless=true` Java launch is the documented Azureus-lineage pattern (NOT exercised in the probe session — smoke-test before packaging).

## Web / remote-control surfaces
- AZMP (Azureus/BiglyBT Messaging Protocol): JSON-RPC built into core, disabled by default, enable in Settings → Connection (default port 8080, user/pass). This is the scripting/integration surface.
- xmwebui plugin (`BiglySoftware/BiglyBT-plugin-xmwebui`, active — also contains a Transmission-RPC-compatible layer, `TransmissionVars.java`) powers the OFFICIALLY HOSTED web front-ends `webremote.biglybt.com` and `bweb.biglybt.com` (both live). The front-end is NOT self-hostable — a third-party SaaS sits in the control path (relay tunnel works NAT-free but exits BiglyBT's servers; poor optics for an I2P-privacy setup).
- BiglyBT Android app is an official full remote.
- Old Vuze-era web UIs (azwebui etc.) are dead.

## I2P
- Official plugin `BiglySoftware/BiglyBT-plugin-azneti2phelper` ("Provides connectivity via the I2P network", active). Not in the base tarball.

## Arr-suite integration — the hard part
- Sonarr/Radarr have NO native BiglyBT download client. Realistic glue paths: azexec post-download command-runner script that pokes the arr's import API, or an AZMP↔Transmission-RPC shim (xmwebui's Transmission-compat code suggests the API shape is close — unverified as a full shim).
- Practical alternative already packaged: qbittorrent_ynh / deluge_ynh (official YunoHost-Apps) for the arr-facing client, BiglyBT only where its I2P/privacy features are actually needed.

## Packaging implication
Java-app packaging shape (JRE runtime, arch-independent source = single `[resources.sources.main]`, no build step). The interesting engineering is the arr glue + plugin vendoring + SSO: AZMP has its own user/pass auth and BiglyBT has no trusted-header hook, so expect a login page behind the portal (cap-style pattern) rather than SSO walk-in.
