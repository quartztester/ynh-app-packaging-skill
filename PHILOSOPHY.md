# The tail is the point

*A YunoHost packaging creed. Why we should package it anyway*

Chris Anderson called it in 2004: "Forget squeezing millions from a few
megahits. The future of entertainment is in the millions of niche markets at
the shallow end of the bitstream."
([Wired](https://www.wired.com/2004/10/tail/)) Kiwix found the same shape in
knowledge: Wikipedia is 15% of its downloads, and 60% of downloads aren't in
the top 500.
([Kiwix](https://hub.kiwix.org/weblog/2024/03/our-very-long-tail/)) The
shelf is not the market. The market is what spills past the shelf.

Self-hosting has the same curve. The ten apps everyone can name are the
head; the people live in the tail, and the YunoHost wishlist holds 515 apps
users have asked for
([`wishlist.toml`](https://github.com/YunoHost/apps/blob/master/wishlist.toml)):
five hundred and fifteen people standing at doors that haven't been built
yet.

## Availability is the moat

A US district court explained in 1999 how Windows beat everybody. Not
quality, not price: shelf depth. The "applications barrier to entry," in the
court's own words: "The fact that a vastly larger number of applications are
written for Windows than for other PC operating systems attracts consumers
to Windows, because it reassures them that their interests will be met."
Apple, with 12,000 applications, could not punch through.
([US v. Microsoft, Findings of Fact](https://www.justice.gov/atr/us-v-microsoft-courts-findings-fact))

People adopt a platform the night they find their one weird thing
installable, certificates and backups and fail2ban already done. Every
unshelved app is a membership the platform never collects. Availability is
not a courtesy. It is the growth strategy, the one a federal court wrote
down while explaining why the biggest software company on earth stayed the
biggest.

## The rival serves the moment and shatters the world

Docker's ten minutes are real: copy the compose file, `up`, it works. But
the ease is per-deployment, and so is everything after it. Every container
is an island; the certificates, backups, upgrades, and midnight
micro-issues are paid alone. People "get 'tired of maintaining their stuff'
and give up"
([Aleks](https://forum.yunohost.org/t/will-yunohost-be-able-to-keep-up-with-all-updates/26739/11)),
and Docker's community is a folder of compose files: patterns to copy, not
infrastructure to inherit.

## The commons is the counter-move

Aleks's arithmetic: if everyone rolling their own stack gave 2% of their
time to "any sort of 'common' self-hosting stack," "we would live in
self-hosting utopia since quite a while." A compose file is a private good;
a `_ynh` package is what the legal scholar Carol Rose called a comedy of the
commons: a resource that does not wear out with use and gains value the more
people use and mend it (53 U. Chi. L. Rev. 711, 1986). One fix lands on
every server running the package, forever.

## Hours were the ceiling. Agents are the lever.

Packaging is real work, and human hours do not scale to a 515-deep queue.
But the format is uniform (one file layout across all 483 active packages,
98% `conf/`, 98% `tests.toml`; catalog audit, October 2026), which is what
makes a package machine-writable. The boring 80% is mechanical; judgment
stays human. The catalog already trusts machines, since quality levels are
bot-assigned from CI and package_check grades every package before a human
looks. The gates care what passes, not who typed. The rest is honesty:
disclose the assistance (the `Assisted-by:` trailer), keep the scripts
legible to the 3 a.m. human, pin and test what you ship.

## The creed of the shelf

- Package the weird one. Maintenance cost is a reason to label a door,
  never to remove it.
- Label the broken one. 26 `notworking` apps stay on the shelf, flagged and
  honest
  ([`apps.toml`](https://github.com/YunoHost/apps/blob/master/apps.toml)).
  A label says: this door sticks, try it anyway.
- Hide the failing one, never delete it. Level 4 or below means
  unadvertised and upgrade-frozen, not gone.
- Bury only the dead. The graveyard holds 131 names, every cause kept
  legible
  ([`graveyard.toml`](https://github.com/YunoHost/apps/blob/master/graveyard.toml)).

## The charge

Serve the head and you compete with Docker for the same ten apps. Serve the
tail and you're the only platform in the room where the people are.

Label, don't delete. Let the machine type; you verify. Give the 2%.

**The tail is the point. Package it anyway.**

---

### Sources

- Chris Anderson, ["The Long Tail"](https://www.wired.com/2004/10/tail/), Wired, 2004-10-01.
- [US v. Microsoft, Court's Findings of Fact](https://www.justice.gov/atr/us-v-microsoft-courts-findings-fact) (1999) — the "applications barrier to entry."
- Kiwix, ["Our (very) Long Tail"](https://hub.kiwix.org/weblog/2024/03/our-very-long-tail/) (2024-03-28) — 15% / 60%.
- Aleks, [YunoHost forum thread 26739, reply 11](https://forum.yunohost.org/t/will-yunohost-be-able-to-keep-up-with-all-updates/26739/11) (2023-10-15) — "tired of maintaining their stuff," the 2% utopia.
- Carol Rose, "The Comedy of the Commons," 53 U. Chi. L. Rev. 711 (1986).
- [YunoHost/apps](https://github.com/YunoHost/apps): `apps.toml`, `wishlist.toml`, `graveyard.toml` — 26 / 515 / 131 (2026-10-30).
- 483-package corpus audit (2026-10-30): uniform script set, 98% `conf/`, 98% `tests.toml`.

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

The ideas are the author's. The footwork was outsourced at roughly 100%,
which is, one might argue, the 2% bargain working as intended.
