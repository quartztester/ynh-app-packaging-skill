# Package It Anyway

*A philosophy of the long tail, the 2% bargain, and why we keep every app on the shelf.*

## The competitor is not another distro

The competitor for a self-hosting platform is not another server OS. It is a
`compose.yaml` — copy, paste, up, works in ten minutes. Docker optimizes the
moment of deployment. Nobody optimizes the eighth month.

The eighth month is where self-hosting actually dies. As Aleks (YunoHost's lead
developer) put it, people "think they can just easily set up their own server by
just spinning a few docker, without realizing that the full life of a server is
also: certificates, backups, fail2ban/security, upgrades, front-end server /
reverse proxy, dns configuration, monitoring/diagnosis, and a shitload of time
debugging countless boring micro-issues."
([forum, 2023-10-15](https://forum.yunohost.org/t/will-yunohost-be-able-to-keep-up-with-all-updates/26739/11))

Every per-deployment stack pays that tax alone. A community pays it once.

## The wheel-reinvention paradox

> "In programming, anybody re-coding what's already done in 10 library will be
> thought of as a madman, yet in the self-hosting community, it seems perfectly
> sensible for everybody to re-setup pretty much the same stack, all with the
> same pitfalls, until ultimately people will get 'tired of maintaining their
> stuff' and give up. […] In the end, if every person implementing their own
> self-hosting stack in their own corner contributed 2% of their time to any
> sort of 'common' self-hosting stack that anybody can easily setup and
> maintain, we would live in self-hosting utopia since quite a while. Instead,
> quite a lot of people are like 'I tried X and Y and Z but none are perfect so
> watch me spend 3 weeks setting up everything by hand myself and giving up 8
> months later.' ¯\\\_(ツ)\_/¯"
> — [Aleks, YunoHost forum](https://forum.yunohost.org/t/will-yunohost-be-able-to-keep-up-with-all-updates/26739/11)

YunoHost is what 2% looks like when it's pooled. A `docker-compose.yml` is a
private good: it serves one box, dies with its author, carries its pitfalls
alone. A `_ynh` package is a public good: every fix, every patch, every
boring login-loop workaround becomes infrastructure for every server running
it. Packaging is not dockerizing with extra steps — it is the decision to stop
renting your stack and start endowing everyone's.

## The tail is not noise. It is the point.

Kiwix, publishing its download stats, found that Wikipedia — the reason most
people think they know Kiwix — is only 15% of downloads, and
"60% of all downloads are not in this top 500. Yes, our long tail is very
long!" ([Our (very) Long Tail, 2024-03-28](https://hub.kiwix.org/weblog/2024/03/our-very-long-tail/))

Self-hosting has the same shape. The app that "nobody really needs" — the one
with the weird build system, the unmaintained upstream, the niche userbase —
is the *entire mass* of the distribution. People do not adopt a platform for
its top-10 apps; they adopt it the night they search for the one weird thing
they actually need and find it installable. Every app on the shelf is an open
door, an invitation to try the whole infrastructure. A shelf pruned to what is
comfortable to maintain is a shelf that quietly stops inviting.

## So: keep it available

Therefore our stance, even where it costs us:

- **An app should be available in some form.** Maintenance overhead is a
  reason to *label* an app — the catalog keeps its states honest (`working`,
  `notworking`, flagged and frozen, never silently removed: 726 apps listed,
  26 admitted-broken still on the shelf,
  [YunoHost/apps](https://github.com/YunoHost/apps/blob/master/apps.toml)) —
  not a reason to hide it. Removal is the message "this door is closed."
  A label is the message "this door sticks; try it anyway."
- **Availability recruits; quality retains.** We ship the door and we
  instrument the sticky parts. A WIP app with honest CI levels teaches more
  than a deleted one, and someone with the exact itch will show up to oil the
  hinges — that is where new maintainers come from.
- **Docker-easy is a fair criticism.** If our stack feels slower to update
  than a `:latest` pull, the answer is not to become Docker; it is to make the
  community's 2% faster — autoupdate bots, CI gates, shared helpers — until
  pooled maintenance beats private maintenance at its own game.
- **Every package you contribute is a donation to strangers' servers, forever.**
  Behave accordingly: pin what you ship, test what you ship, leak nothing,
  disclose your AI assistance, and leave the scripts legible to the maintainer
  who inherits them at 3 a.m.

## The bargain

You will not have a perfect stack. Nobody's is. The choice is whether the
imperfection is *shared* — one bug fixed once, on everyone's shelf at once —
or *private*, suffered alone for eight months until you give up and the server
goes dark.

Give the 2%. Keep every door open. The long tail is where the people are.

---

### Sources

- Aleks, "Will YunoHost be able to keep up with all updates?",
  [YunoHost forum thread 26739](https://forum.yunohost.org/t/will-yunohost-be-able-to-keep-up-with-all-updates/26739/11), 2023-10-15 — quotes #11; the thread's
  opening post is itself a Docker refugee asking why the shared stack is slow,
  which is exactly the tension this document lives in.
- Kiwix Hub, ["Our (very) Long Tail"](https://hub.kiwix.org/weblog/2024/03/our-very-long-tail/), 2024-03-28 — the shape of content demand.
- [YunoHost/apps `apps.toml`](https://github.com/YunoHost/apps/blob/master/apps.toml) — catalog states as published policy (counts verified 2026-10-30).
- [YunoHost packaging docs](https://doc.yunohost.org/en/dev/packaging/) — the quality-level machinery that makes "labeled, never hidden" possible.

---

## Appendix: how this document came to exist

For the record — and as evidence of the author's magnificent laziness — the
entire commissioning prompt was:

> I also want you to write a small philosophy.md
>
> Essentially, I believe it is crucial that all apps regardless of maintenance
> overhead should at-least be available in some form to incentivize people to
> come over and try out the yunohost infrastructure to gain more community
> members. Our main competition is docker, which incentivizes per deployment
> easyness of upgrade and new features but a fragmented community of all-in-one
> boxes that yunohost just does better given its community focus. […]
>
> It should be short suite and concise like a manifesto. Title can be whatever
> but make it emotional.
>
> Also feel free to put the raw prompt at the bottom of the manifesto so people
> can see my laziness. I don't care. Lol.

*(The middle of the prompt was a copy-paste of the Aleks forum quote above,
with links. The writing agent verified the forum post, pulled the Kiwix stats,
and crawled the catalog states itself. The ideas are the author's; the footwork was
outsourced at roughly 100% — which is, one might argue, the 2% bargain working
as intended.)*
