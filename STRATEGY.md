# Two-front strategy

*Companion to PHILOSOPHY.md. The creed says package the tail anyway; this
says where to spend the hours first.*

## Front 1 — the steady shelf (long-term stable apps)

Mature, slow-moving upstreams. Low churn, few API breakages, cheap to keep
green. Every one of these is maintenance other volunteers and maintainers
never inherit. Depth here is what makes the platform trustworthy enough to
stay on — the shelf that reassures (see *US v. Microsoft* in PHILOSOPHY.md).

## Front 2 — the rising shelf (new and upcoming apps)

New, hyped, growing upstreams. This is where traction is won: people adopt a
platform the night they find their new favorite thing installable. Higher
risk — APIs shift, packages break, dependencies move under you. So: pin
sources, keep `autoupdate` ready, test the lifecycle gates honestly, and
label rather than delete when upstream wobbles.

## The balance

Front 1 buys the future; Front 2 gets noticed this year. When the two
compete for an hour, Front 1 keeps the doors working — and broken doors cost
more than missing ones.

## The third front — the world finds out

A package nobody knows about installs nobody. Every catalog addition is a
visibility event for the whole platform, and it is wasted the moment it
merges silently. AI-assisted packaging buys hours; those hours are spent on
the announcement, not on packaging one more app. The volume AI enables is
only ever volume *after* the quality gates — a shipped slop package costs
the platform more trust than a missing one (levels ≤4 get hidden and
frozen), and the announcement list is what keeps that honest: you only
announce what you would defend in front of the upstream maintainer.

When a package lands in the catalog:
- Post the announcement thread on the YunoHost forum — that is where
  adoption actually starts.
- Tell the upstream project their app is installable on YunoHost. Their
  link back is the only SEO that compounds.
- One screenshot or short demo GIF. Nobody shares a manifest.
- Social post where the app's community actually lives.

Front 1 keeps the doors working. Front 2 gives the world a reason to look.
This front is the one that makes them see it.

---

## Appendix: the raw prompt

Verbatim, laziness included:

> Make a STRATEGY.md on the packaging skill that I have a two fold strategy
>
> - long term stable applications to increase usage and reduce maintenance
>   from other volunteers and maintainers
> - target new and upcoming apps to gain general traction. Will have to be
>   careful here as there is a higher risk of api and packages breaking.
>
> Make it extremely short and read the philosophy.md for reference
>
> Include my raw prompt in the doc

Second commissioning prompt, verbatim (2026-11-02, the third front):

> On my yunohost packaging skill - on my strategy.md. The use of AI is meant
> to add seo to the platform and not over slop everything. If a new package
> is added, I'd like to world to know.
