# The Tail Is the Point

*A YunoHost packaging creed.*

Wikipedia is 15% of Kiwix's downloads. The famous thing — the reason you think
you know Kiwix — serves one download in seven. **60% of downloads aren't in
the top 500.** The long tail is not the edge of the demand curve. It *is* the
demand curve. ([Kiwix, "Our (very) Long
Tail"](https://hub.kiwix.org/weblog/2024/03/our-very-long-tail/))

Every software shelf has this shape. We build for the head — the ten apps
everyone can name — and the people live in the tail: the federation tool, the
niche dashboard, the thing with eleven users worldwide. Self-hosting lives
hardest in the tail, and the YunoHost catalog carries the receipt: **515
apps** sit in
[`wishlist.toml`](https://github.com/YunoHost/apps/blob/master/wishlist.toml)
— five hundred and fifteen people standing at a door that hasn't been built
yet. Nobody adopts a platform for its top ten apps. They adopt it the night
they search for their one weird thing and find it installable — certificates,
backups, fail2ban already done. The door is the product.

The tail is not the margin of this project. The tail is the point.

## What the tail costs

Packaging is real work: manifest, six lifecycle scripts, nginx conf, systemd
unit, CI — and upgrades forever after. The shelf exists because hundreds of
humans donated those hours. But the queue is 515 deep, and human hours do not
scale to a tail this long. That is the honest reason shelves get pruned and
"maintenance overhead" becomes a reason to say no: not malice — arithmetic.
Triage is how the tail dies.

## What an unserved tail costs

Somebody needs their one weird app. The commons doesn't have it yet. Docker
Hub does — ten minutes, copy the compose file, `up`, and the seduction works.
So they don't join the commons; they hand-roll the entire wheel to get the
one spoke they wanted. And the wheel is never just the app: certificates,
backups, fail2ban, DNS, upgrades, monitoring, a shitload of boring
micro-issues at midnight. Docker optimizes the moment of deployment. Nobody
— **nobody** — optimizes the eighth month.
([Aleks, YunoHost forum](https://forum.yunohost.org/t/will-yunohost-be-able-to-keep-up-with-all-updates/26739/11))

Aleks has watched this graveyard fill for years: people "get 'tired of
maintaining their stuff' and give up." His arithmetic is the repair — if
everyone rolling their own stack gave **2% of their time to a common one**,
"we would live in self-hosting utopia since quite a while." A compose file
is a private good: it serves one box and dies with its author. A `_ynh`
package is a public good: every fix becomes infrastructure on every server
running it. Every unshelved wishlist entry is a future defector to solo
stack-rolling. The queue is the leak.

## How the tail gets shelved

The 2% has a bottleneck: hours. Hours now have a lever.

The packaging format is uniform — one file layout across all 483 active
packages (same script set, 98% `conf/`, 98% `tests.toml`; 2026-10 audit),
shared helpers, standard CI. That uniformity is not bureaucracy; it is what
makes a package machine-writable. The boring 80% — scaffolding, manifest
fields, the nginx conf, the upgrade path — is mechanical, and mechanical
work is what machines are for. The judgment stays human: real
configurations, live-box installs, upgrade proofs, review. One maintainer
with an agent shelves what one maintainer alone never could.

And the trust problem is already solved, because the catalog already trusts
machines: quality levels are bot-assigned from CI, and package_check grades
every package before any human looks at it. A machine may *judge* every
package; a machine helping *write* one is not a category change. The gates
do not care who typed — they care what passes. Honesty is the obligation:
disclose the assistance (the `Assisted-by:` trailer), keep the scripts
legible to the 3 a.m. human, pin what you ship, test what you ship.

## The creed of the shelf

- **Package the weird one.** Maintenance cost is a reason to label a door,
  never to remove it. Someone with the exact itch will show up to oil the
  hinges — that is where maintainers come from.
- **Label the broken one.** The catalog keeps 26 `notworking` apps on the
  shelf, flagged and honest
  ([`apps.toml`](https://github.com/YunoHost/apps/blob/master/apps.toml)).
  A label says: *this door sticks; try it anyway.*
- **Hide the failing one — never delete it.** Quality level ≤4 means
  unadvertised and upgrade-frozen, not gone. Anyone who knows can still
  install.
- **Bury only the dead.** When the last maintainer walks away, the app moves
  to [`graveyard.toml`](https://github.com/YunoHost/apps/blob/master/graveyard.toml)
  — 131 graves, every name and cause kept legible. We do not pretend doors
  never existed. We mark the ones that stick.

## The charge

Serve the head and you compete with Docker for the same ten apps. Serve the
tail and you are the only ones in the room where the people are.

Label, don't delete. Let the machine type; you verify. Give the 2%.

**The tail is the point. Package it anyway.**

---

### Sources

- Kiwix, ["Our (very) Long Tail"](https://hub.kiwix.org/weblog/2024/03/our-very-long-tail/) (2024-03-28) — 15% / 60%.
- Aleks, [YunoHost forum thread 26739, reply 11](https://forum.yunohost.org/t/will-yunohost-be-able-to-keep-up-with-all-updates/26739/11) (2023-10-15) — the eighth-month list, "tired of maintaining their stuff," the 2% utopia.
- [YunoHost/apps](https://github.com/YunoHost/apps): `apps.toml`, `wishlist.toml`, `graveyard.toml` — 26 flagged / 515 queued / 131 buried (2026-10-30).
- 483-package corpus audit (2026-10-30): uniform script set, 98% `conf/`, 98% `tests.toml` — the uniformity that makes packages machine-writable.
- [yunohost.org](https://yunohost.org/) — "digital services (apps) that you control."

---

## Appendix: the raw prompt

For the record, and as evidence of the author's magnificent laziness, the
entire commissioning prompt — verbatim:

> I also want you to write a small philosophy.md
>
> Essentially, I believe it is crucial that all apps regardless of maintenance
> overhead should at-least be available in some form to incentivize people to
> come over and try out the yunohost infrastructure to gain more community
> members. Our main competition is docker, which incentivizes per deployment
> easyness of upgrade and new features but a fragmented community of all-in-on
> boxes that yunohost just does better given its community focus. Per
> https://forum.yunohost.org/t/will-yunohost-be-able-to-keep-up-with-all-updates/26739/11
> *[the Aleks forum quote, pasted here in full — see the link]* This is based
> from https://hub.kiwix.org/weblog/2024/03/our-very-long-tail/. Feel free to
> do deep research and find other places to quote, I like citations and
> authoritative sources like the yunohost forums.
>
> It should be short suite and concise like a manifesto. Title can be whatever
> but make it emotional.
>
> Also feel free to put the raw prompt at the bottom of the manifesto so people
> can see my laziness. I don't care here. Lol. Include this section. (Don't
> include the raw quote here, just the link).

The ideas are the author's. The footwork was outsourced at roughly 100% —
which is, one might argue, the 2% bargain working as intended.
