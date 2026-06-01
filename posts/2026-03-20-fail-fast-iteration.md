---
title: "Fail fast, but fail informatively"
date: 2026-03-20
tags: [product, engineering, consulting]
description: "Failing fast is good advice. Failing without capturing what you learned is waste."
---

Fail fast is one of those phrases that's been repeated enough to lose meaning. The intent is right — don't sink months into something before testing your assumptions. But in practice I see teams treat failure as the goal rather than the feedback.

## What failing fast is actually for

The point isn't to fail. It's to get signal cheaply. You build the smallest thing that can answer the question you're actually afraid of, you run it, and you use the result to make a better decision.

The common mistake is treating "we shipped quickly" as success when the thing shipped didn't actually test anything meaningful. A login page deployed in a week tells you nothing about whether anyone wants what's behind it.

## The thing nobody writes down

When something doesn't work, teams move on. The next sprint starts, the board gets cleared, and the learning is in someone's head until they leave.

The most valuable consulting work I do is sometimes just asking: what did you learn from that? And writing it down somewhere findable.

It doesn't need to be an ADR. A Slack message copied into a doc is better than nothing. The question is: if someone joins this team in six months, will they know not to try this again, and why?

## Failing informatively

The checklist I use when something doesn't go to plan:

- What assumption did we make that turned out wrong?
- Was there signal earlier that we missed or ignored?
- What would we do differently given the same starting information?
- What would we do differently given what we know now?

That last distinction matters. Don't punish people for not knowing things they couldn't have known. Do ask why the process didn't surface the signal sooner.

## On consulting engagements specifically

Clients often want certainty. The job is helping them see that a well-designed failure is cheaper than a prolonged uncertain success. A two-week spike that definitively rules out an approach saves months of hedged, tentative progress.

The pitch isn't "let's fail." It's "let's find out quickly, whatever the answer is."
