# The tail is the point

*A YunoHost packaging creed. Why we should package it anyway*

Chris Anderson saw it first, in 2004, about music and books: "Forget
squeezing millions from a few megahits. The future of entertainment is in
the millions of niche markets at the shallow end of the bitstream."
([Wired](https://www.wired.com/2004/10/tail/)) He had the numbers, too. The
average Barnes & Noble carries 130,000 titles; more than half of Amazon's
book sales come from outside its top 130,000. The shelf is not the market.
The market is what spills past the shelf.

Kiwix found the same shape in offline knowledge: Wikipedia, the reason you
think you know Kiwix, is 15% of downloads, and 60% of downloads aren't in
the top 500.
([Our (very) Long Tail](https://hub.kiwix.org/weblog/2024/03/our-very-long-tail/))
Self-hosting has the same curve. The ten apps everyone can name are the
head. The people live in the tail: the federation tool, the niche dashboard,
the thing with eleven users worldwide.

## Availability is the moat

A United States district court named the mechanism in 1999, while explaining
how Windows beat everybody. Not quality, not price: shelf depth. The court
called it the "applications barrier to entry" and described it in one
sentence: "The fact that a vastly larger number of applications are written
for Windows than for other PC operating systems attracts consumers to
Windows, because it reassures them that their interests will be met." Apple,
with 12,000 applications on its shelf, still could not punch through.
([US v. Microsoft, Findings of Fact](https://www.justice.gov/atr/us-v-microsoft-courts-findings-fact))

Read that again with self-hosting in mind. People do not adopt a platform
for its top ten apps. They adopt it the night they search for their one
weird thing and find it installable, with certificates and backups and
fail2ban already done. The YunoHost wishlist holds 515 apps users have asked
for
([`wishlist.toml`](https://github.com/YunoHost/apps/blob/master/wishlist.toml)):
five hundred and fifteen people standing at doors that haven't been built
yet. Every unshelved app is a membership the platform never collects.
Availability is not a courtesy. It is the growth strategy, the one a federal
court wrote down while explaining why the biggest software company on earth
stayed the biggest.

## The rival serves the moment and shatters the world

Docker's pitch is real, and we should stop pretending otherwise. Ten
minutes: copy the compose file, `up`, and it works. But the ease is
per-deployment, and so is everything after it. Every container is an island.
The certificates, the backups, the upgrades, the reverse proxy, the DNS, the
countless boring micro-issues at midnight: every box pays that tax alone.
Aleks, YunoHost's lead developer, has watched the result for years. People
"get 'tired of maintaining their stuff' and give up."
([forum](https://forum.yunohost.org/t/will-yunohost-be-able-to-keep-up-with-all-updates/26739/11))

And Docker's community, such as it is, is a folder of compose files:
patterns to copy, not infrastructure to inherit. Per-deployment ease buys
per-deployment everything. A million all-in-one boxes are born fragmented.

## The commons is the counter-move

YunoHost's answer is not better per-deployment ease. It is the commons.
Aleks's arithmetic: if every person rolling their own stack in their own
corner contributed 2% of their time to "any sort of 'common' self-hosting
stack that anybody can easily setup and maintain," "we would live in
self-hosting utopia since quite a while." A compose file is a private good:
it serves one box and dies with its author. A `_ynh` package is closer to
what the legal scholar Carol Rose called a comedy of the commons: a resource
that does not wear out with use and grows more valuable the more people use
and mend it (53 U. Chi. L. Rev. 711, 1986). One maintainer's fix lands on
every server running the package, forever. The 483 packages on the shelf
exist because hundreds of humans donated those hours, and each hour is still
paying rent on strangers' servers.

## Hours were the ceiling. Agents are the lever.

The honest reason shelves get pruned is arithmetic. Packaging is real work:
manifest, six lifecycle scripts, nginx conf, systemd unit, CI, and upgrades
forever after. Human hours do not scale to a 515-deep queue. But the format
is uniform (one file layout across all 483 active packages, 98% `conf/`,
98% `tests.toml`; we audited the catalog in October 2026), and that
uniformity is exactly what makes a package machine-writable. The boring 80%
is mechanical work, and machines are for mechanical work. The judgment stays
human: real configurations, live-box installs, upgrade proofs, review.

The trust question answers itself if you look at what the catalog already
does. Quality levels are bot-assigned from CI, and package_check grades
every package before any human looks at it. The gates care what passes, not
who typed. The obligations that remain are honesty ones: disclose the
assistance (the `Assisted-by:` trailer), keep the scripts legible to the
3 a.m. human, pin what you ship, test what you ship.

## The creed of the shelf

- Package the weird one. Maintenance cost is a reason to label a door,
  never to remove it. Someone with the exact itch shows up eventually to oil
  the hinges, and that's where maintainers come from.
- Label the broken one. The catalog keeps 26 `notworking` apps on the
  shelf, flagged and honest
  ([`apps.toml`](https://github.com/YunoHost/apps/blob/master/apps.toml)).
  A label says: this door sticks, try it anyway.
- Hide the failing one, never delete it. Quality level 4 or below means
  unadvertised and upgrade-frozen, not gone. Anyone who knows can still
  install.
- Bury only the dead. When the last maintainer walks away, the app moves to
  [`graveyard.toml`](https://github.com/YunoHost/apps/blob/master/graveyard.toml),
  131 graves, every name and cause kept legible. We don't pretend doors
  never existed; we mark the ones that stick.

## The charge

Serve the head and you compete with Docker for the same ten apps. Serve the
tail and you're the only platform in the room where the people are, and a
federal court has already explained what happens to the platform whose shelf
those people can rely on.

Label, don't delete. Let the machine type; you verify. Give the 2%.

**The tail is the point. Package it anyway.**

---

### Sources

- Chris Anderson, ["The Long Tail"](https://www.wired.com/2004/10/tail/), Wired, 2004-10-01 — niche markets, Amazon outside the top 130,000.
- [US v. Microsoft, Court's Findings of Fact](https://www.justice.gov/atr/us-v-microsoft-courts-findings-fact) (1999) — the "applications barrier to entry," the shelf-depth sentence, Apple's 12,000 apps.
- Kiwix, ["Our (very) Long Tail"](https://hub.kiwix.org/weblog/2024/03/our-very-long-tail/) (2024-03-28) — 15% / 60%.
- Aleks, [YunoHost forum thread 26739, reply 11](https://forum.yunohost.org/t/will-yunohost-be-able-to-keep-up-with-all-updates/26739/11) (2023-10-15) — "tired of maintaining their stuff," the 2% utopia.
- Carol Rose, "The Comedy of the Commons: Custom, Commerce, and Inherently Public Property," 53 U. Chi. L. Rev. 711 (1986) — nonrival goods that gain value with use.
- [YunoHost/apps](https://github.com/YunoHost/apps): `apps.toml`, `wishlist.toml`, `graveyard.toml` — 26 flagged / 515 queued / 131 buried (2026-10-30).
- 483-package corpus audit (2026-10-30): uniform script set, 98% `conf/`, 98% `tests.toml`.
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

The ideas are the author's. The footwork was outsourced at roughly 100%,
which is, one might argue, the 2% bargain working as intended.
