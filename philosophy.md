# Package It Anyway

*A YunoHost packaging creed.*

Docker gives you ten minutes. The eighth month kills you.

Ten minutes: copy the compose file, `up`, and it works — the seduction is real,
we concede it. Then the certificates expire. The backups silently stop.
fail2ban isn't watching this one. DNS doesn't resolve. The reverse proxy
fights the app. Upstream ships a breaking tag. And every one of those boring
micro-issues is yours, alone, at midnight — because your stack was built for
the moment of deployment and nobody, **nobody**, optimizes the eighth month.
([Aleks, YunoHost forum](https://forum.yunohost.org/t/will-yunohost-be-able-to-keep-up-with-all-updates/26739/11))

Aleks, who builds YunoHost, has watched this graveyard fill for years: people
"get 'tired of maintaining their stuff' and give up." His arithmetic is the
whole creed — if every person rolling their own stack gave **2% of their time
to a common one**, "we would live in self-hosting utopia since quite a while."
Instead they spend three weeks building it alone and eight months regretting
it. Every per-deployment stack pays the tax alone. A community pays it once.

A compose file is a private good: it serves one box, dies with its author, and
carries its pitfalls to the grave. A `_ynh` package is a public good: every
fix you land becomes infrastructure on every server running it, forever.
Packaging is not dockerizing with extra steps. It is the decision to stop
renting your stack and start endowing everyone's.

## The tail is the point

Kiwix publishes its numbers: Wikipedia — the reason you think you know Kiwix —
is **15% of downloads**. **60% of downloads aren't in the top 500.** The long
tail is not the edge of the demand curve. The long tail *is* the demand curve.
([Our (very) Long Tail](https://hub.kiwix.org/weblog/2024/03/our-very-long-tail/))

Self-hosting has the same shape, and the YunoHost catalog carries the receipt:
**515 apps** sit in
[`wishlist.toml`](https://github.com/YunoHost/apps/blob/master/wishlist.toml)
— five hundred and fifteen people standing at the door, waiting for the one
weird thing they actually need. Nobody adopts a platform for its top ten
apps. They adopt it the night they search for the niche app nobody bothered
to package — and find it installable, with certificates and backups and
fail2ban already done. The door is the product; YunoHost's own sentence says
so — digital services *that you control*, with very little technical
knowledge. A shelf pruned to what is comfortable to maintain is a shelf that
quietly stops inviting.

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

You will never have a perfect stack. Nobody's is. The only question is
whether the imperfection is **shared** — one bug, fixed once, on everyone's
shelf at once — or **private**, suffered alone until you give up and the
server goes dark.

And yes, Docker is easier on day one. The answer is not to become Docker. It
is to make the community's 2% faster — autoupdate, CI gates, shared helpers —
until pooled maintenance beats private maintenance at its own game.

When you package, remember what you are doing: donating your nights to
strangers' servers, forever. Pin what you ship. Test what you ship. Leak
nothing. Disclose your AI. Leave the scripts legible to whoever inherits them
at 3 a.m.

Give the 2%. Keep every door open. **Package it anyway.**

---

### Sources

- Aleks, [YunoHost forum thread 26739, reply 11](https://forum.yunohost.org/t/will-yunohost-be-able-to-keep-up-with-all-updates/26739/11) (2023-10-15) — the eighth-month list, "tired of maintaining their stuff," the 2% utopia.
- Kiwix, ["Our (very) Long Tail"](https://hub.kiwix.org/weblog/2024/03/our-very-long-tail/) (2024-03-28) — 15% / 60%.
- [YunoHost/apps](https://github.com/YunoHost/apps): `apps.toml`, `wishlist.toml`, `graveyard.toml` — 26 flagged / 515 queued / 131 buried (2026-10-30).
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

The ideas are the author's. The footwork was outsourced at roughly 100% — which is,
one might argue, the 2% bargain working as intended.
