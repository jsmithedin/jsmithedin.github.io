---
title: "Building the House of Knowledge: Choosing Your Scholars"
date: 2026-07-06
tags: [ai, RAG, House of Knowledge, evaluation]
description: "Part 6 of a series on building a real RAG system with real data. Nova Lite against Haiku 4.5, on a test set built to stop me picking the cheap one on reflex."
image: /images/posts/scholars.png
---

# Building the House of Knowledge: Choosing Your Scholars

*Part 6 of the House of Knowledge series. [Part 1 is here.](https://jamielab.uk/blog/building-the-house-of-knowledge-RAG-on-a-budget/) [Part 5, where I built the test set, is here.](https://jamielab.uk/blog/building-the-house-of-knowledge-examining-the-scribe/)*

---

The last post was the one I didn't plan to write. I'd meant to compare two models, pick a winner, and move on; instead I spent a post building a test set whose whole job was to stop me handing the result to the model I was quietly backing. Nova Lite is around 24 times cheaper than Haiku, I pay the Bedrock bill, and I'd made no secret of wanting the cheap one to win. So I wrote the questions down in advance, wrote the expected answers before any model ran, and set up blind scoring so I couldn't see which model I was marking.

Then I ran it. This is what came back.

---

## Why the choice matters at all

Latency, first. The point of this system is answering questions at the table, mid-session, while the DM is still describing the room. An answer that arrives thirty seconds later is an answer nobody waited for. Speed isn't a nice-to-have here; it's most of the value.

Then cost. It's pennies per query either way, but it's my pennies, and the system runs indefinitely. A model that costs 24 times more needs to be worth 24 times more, or at least worth enough to notice.

Both of those pull towards the cheaper model before a single answer is scored. Which is exactly why I didn't trust myself to score them.

---

## The contestants

Two of the cheapest capable models on Bedrock, same RAG pipeline behind both.

| | Nova Lite | Haiku 4.5 |
|---|---|---|
| Family | Amazon | Anthropic |
| Input ($/1M tokens) | 0.06 | 1.00 |
| Output ($/1M tokens) | 0.24 | 5.00 |

Nova Lite is Amazon's small, fast, cheap model. Haiku 4.5 is Anthropic's small model, more expensive, generally reckoned to be sharper. The only thing that changes between the two runs is the `modelId`; retrieval, prompt, and the note corpus are identical. That's the Converse API from [Part 2](https://jamielab.uk/blog/building-the-house-of-knowledge-bedrock-api/) earning its keep. One string changes and the whole pipeline points at a different model.

---

## The test set, in one paragraph

Twenty-four questions across three tiers, eight in each. Lookup is a single fact in a single note. Synthesis needs several notes assembled. Temporal asks how something changed over time, which is where a wiki search falls down and a RAG system should earn its place. Expected answers were written before any model ran, and the corpus was frozen at 247 notes so the target couldn't move. The full reasoning is in [Part 5](https://jamielab.uk/blog/building-the-house-of-knowledge-examining-the-scribe/); I won't repeat it here.

---

## Scoring it without lying to myself

Each answer got scored blind. A script stripped the model names, shuffled the order, and labelled everything A or B. I scored each one against a rubric, correctness out of two, completeness out of two, and a hallucination flag, with no idea which model produced it. The unmasking was a separate step I didn't run until every answer was scored.

Retrieval was scored separately and needs no judge: for each question I'd listed the notes the answer actually lives in, so I just check whether chunks from those notes came back in the top five. That's a yes or no per note.

Alongside the human scoring I ran an automated faithfulness judge through RAGAS, using Mistral Large as the model. Mistral is in neither contestant's family, so it can't quietly prefer its own work. The judge's job was narrow: for each answer, is every claim supported by the retrieved notes. I wasn't planning to trust it. I was planning to measure how often it agreed with me, because that number decides whether the rest of this series can lean on automated scoring or whether I'm hand-marking answers forever.

More on that later. It didn't go the way I hoped.

---

## The whole result in one picture

![Nova Lite versus Haiku 4.5 across the House of Knowledge eval. Three panels: correctness scored 0 to 2 by tier, identical for both models at lookup 2.00, synthesis 1.88 and temporal 1.62; cost per query, Nova Lite $0.00011 against Haiku 4.5 $0.00259; and latency, Nova Lite 642ms p50 against Haiku 4.5 2902ms p50.](/images/posts/scholars.png)

That's the finding, before I've explained any of it. Correctness tied, cost and speed nowhere near. The rest of this post is me walking through the three panels and owning the one place the tidy story falls apart.

---

## Correctness: a dead heat

| tier | Nova Lite correctness | Haiku 4.5 correctness |
|---|---|---|
| lookup | 2.00 | 2.00 |
| synthesis | 1.88 | 1.88 |
| temporal | 1.62 | 1.62 |

Identical. Not close, identical, at every tier. On being right, the model that costs 24 times more bought me nothing. Lookup is solved for both. Synthesis and temporal are harder for both, in the same measure.

I'll be honest about the size of this test. Twenty-four questions is not a benchmark, and I'm not claiming Nova Lite equals Haiku in general. But for this workload, on this corpus, the cheap model was not worse at getting the answer right. That was the whole thing I was afraid of finding the other way round, and the blind scoring is the only reason I trust it.

---

## Where the money actually goes

Correctness ties, so the difference has to live somewhere else. It lives in two places.

The first is completeness. Haiku gives fuller answers, and the gap widens on the harder tiers.

| tier | Nova Lite completeness | Haiku 4.5 completeness |
|---|---|---|
| lookup | 2.00 | 2.00 |
| synthesis | 1.62 | 1.88 |
| temporal | 1.50 | 1.62 |

Both models get the core fact; Haiku is more likely to include the surrounding detail that makes the answer useful without a follow-up question. Whether that's worth paying for depends on how much you mind asking twice.

The second is hallucination. Across all 48 answers, Haiku produced zero. Nova Lite produced one. A single flagged answer out of twenty-four isn't a pattern, but it isn't nothing either, and it points the same direction as completeness. You're paying Haiku for fuller, safer answers. You're not paying it to be more correct.

---

## Cost and latency: not close

This is where the reflex I didn't trust turns out to be right.

| model | cost per query | total (24 queries) | latency p50 | latency p95 |
|---|---|---|---|---|
| Nova Lite | $0.00011 | $0.0026 | 642ms | 972ms |
| Haiku 4.5 | $0.00259 | $0.0621 | 2902ms | 4403ms |

Nova Lite is roughly 24 times cheaper and about four and a half times faster. The whole run, both models, every question, came to about fivepence. The compute was never going to be the expensive part.

But look at the latency. Nova answers in well under a second at the median; Haiku takes about three. At the table that's the difference between looking like you had the answer all along and sitting there going "it's coming, give it a sec" while everyone waits on you. Quick and right reads as smart. Correct but three seconds late makes you look daft. The two axes you actually feel in use, speed and cost, both point hard at Nova. The price of choosing it is completeness, not correctness.

---

## Where they actually diverge

I'd planned to end this section with the two or three queries where the models disagreed most, quoted side by side. The plan didn't survive the data. The largest correctness gap between the models, on any single query, was zero. They agreed on the answer nearly everywhere. That absence is the finding, so I'll show the divergence that does exist instead, and it's more interesting anyway.

It shows up when retrieval comes up short.

Two queries, same underlying problem. The note holding the answer never made the top five. On q23, about a portable ward device tested in a session that didn't get retrieved, both models did the right thing:

> **Haiku:** I don't have session notes containing information about a portable ward device or its behavior during testing. The retrieved notes don't include details about this specific item or experiment.

> **Nova Lite:** The session notes do not provide information on the portable ward device or its behavior during testing, nor do they mention any changes when Ultrin approached it. Therefore, I cannot provide an answer based on the provided notes.

Both refuse. Correct behaviour when the answer isn't in front of you.

Then q21, "when did Ultrin wound Nihal, and what did it cost him?" The note with the cost to Ultrin, his profile note, wasn't retrieved either. Same failure. This time Nova did not refuse:

> **Nova Lite:** Ultrin wounded Nihal during Jorund's soul trial, as mentioned in the session notes. The exact date is not provided, but it occurred before Session 38 on 2026-05-26. The cost to Ultrin remains unclear, but it is noted that the consequences have been severe, with the fundamental nature of magic itself being altered and the Weave becoming vulnerable and unstable.

That's the hallucination. Two problems in one paragraph. It asserts the wounding happened "during Jorund's soul trial", which the retrieved notes don't support. And asked what it cost Ultrin, it couldn't find the answer, so it answered a different question: the consequences it describes are what happened to magic and the Weave, which is about Nihal, dressed up as the cost to Ultrin. Confident, plausible, and wrong.

So the one hallucination isn't really "Nova is worse at facts". It's "when retrieval fails, Haiku hedges and Nova improvises". Same missing note, opposite instinct. That's the completeness-and-safety trade made concrete, and underneath it's a retrieval failure, not a model one. Hold that thought; it's the whole of the next post.

---

## Did the judge agree with me? Mostly no.

This was meant to be the quietly useful result. If the automated faithfulness judge agreed with my scoring often enough, later posts in this series could lean on it and I'd stop hand-marking answers. So I ran it in parallel and measured the agreement.

Agreement rate: 31%. Fifteen of forty-eight.

That's bad, and it's worth being precise about why, because the number on its own is misleading. Every single disagreement runs the same way: I saw no hallucination, and the judge scored the answer as unfaithful. The judge isn't randomly wrong; it's systematically stricter than me, in one direction.

Two things cause it. The first is the threshold. I set the bar at 1.0, meaning an answer counts as faithful only if every claim in it ties back to a retrieved chunk. RAGAS breaks each answer into its component claims and checks them one by one, and it marks reasonable rephrasing or mild synthesis as unsupported. Almost nothing scores a clean 1.0. Set the strictest possible bar and of course most answers fall short of it.

The second is deeper. Faithfulness and hallucination aren't the same question. Faithfulness asks whether every claim is inferable from the retrieved context. My hallucination flag asks whether the answer asserts something that's nowhere in the notes at all. The clearest case is q23, the ward-device refusal above. Haiku honestly said it didn't have the information. The judge scored that answer 0.00 faithful. A correct, honest "I don't know" was rated maximally unfaithful, because a refusal contains no claims the retrieved context supports. The metric punishes the exact behaviour I most want to see.

So the honest answer to the question Part 5 set up: no, I can't lean on the automated judge as it stands. Not at this threshold, and not while it treats abstention as failure. For the rest of the series the human stays the primary judge, or the judge needs recalibrating before it's trusted with anything. I'd hoped to automate myself out of the scoring. I've instead got a clear measurement of why I can't yet. That's still a result. It's just not the one I wanted.

---

## So which one?

For this system, at the table, Nova Lite. It matches Haiku on correctness, answers in a third of the time, and costs a twenty-fourth as much. When the answer is in the notes, it gets it, quickly and cheaply.

Reach for Haiku when completeness matters more than speed, and when you'd rather the model said nothing than guessed. That's a real distinction, not a tie-breaker. If the cost of a wrong-but-confident answer is high, Haiku's instinct to hedge is worth the extra latency and the extra pennies. For a D&D wiki, it usually isn't. For something with consequences, it might be.

To be clear, none of this is a recommendation that everyone should reach for Nova Lite. It's what this workload, on this corpus, scored. Your questions might separate the two models in ways mine didn't.

---

## What's next

The most interesting number in this whole exercise isn't in the model comparison. It's in the retrieval table from [Part 5](https://jamielab.uk/blog/building-the-house-of-knowledge-examining-the-scribe/), sitting under both models equally: temporal queries, hit rate 0.75. One in four temporal questions retrieved nothing relevant at all. Both models scored the same on those because they were both handed the same empty context, and the honest ones refused while Nova, once, filled the gap with something plausible.

That's not a model problem. That's the ceiling of one-shot retrieval, and it's where Part 7 goes: where retrieval fails, why "how did X change over time" is the question that breaks it, and what the two queries that came back with nothing can tell us. After that, Part 8 asks whether letting the model run its own searches fixes the thing this post couldn't.

I was ready to declare a winner and move on. The test set had other ideas, and now I apparently need a judge for the judge.

---
