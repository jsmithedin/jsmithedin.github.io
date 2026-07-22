---
title: "Building the House of Knowledge: The Thinking Archivist"
date: 2026-07-22
tags: [ai, RAG, House of Knowledge, evaluation]
description: "Part 8 of a series on building a real RAG system with real data. Letting the model search for itself, and finding out that 'search again' isn't the same thing as 'search better'."
image: /images/posts/archivist.png
---

# Building the House of Knowledge: The Thinking Archivist

*Part 8 of the House of Knowledge series. [Part 1 is here.](https://jamielab.uk/blog/building-the-house-of-knowledge-RAG-on-a-budget/) [Part 7, where retrieval fails, is here.](https://jamielab.uk/blog/lost-in-the-stacks/)*

---

Part 7 ended on a specific question, not a vague one. The ward-device query, q23, never got the right note into its top five at any k I tried, up to fifteen. The theory was that this was a different kind of failure to the budget-hogging ones: not "the answer is in there somewhere, ranked too low," but "the query and the right chunk don't share enough vocabulary for the ranking to ever put them together." A wider net doesn't fix that. Deciding to search again, differently, might. So I asked, directly: given the tool, would the model know to search "2026-06-09 ward device" as a second, narrower attempt, once the first broad search came back full of confident nonsense?

The honest answer is: sometimes it tries something like that, and it still doesn't work. That's a more interesting result than either a clean yes or a clean no, and it's most of this post.

---

## What agentic actually means here

Everything so far has been one retrieval pass: embed the question, pull the top k chunks, hand them to the model, done. Agentic mode gives the model a tool, `search_knowledge_base(query, k)`, and lets it call it as many times as it wants before answering, up to five rounds. The model sees the results of one search and decides whether to search again, search differently, or answer. That's the entire idea. No planning step, no separate retrieval agent, just the same model with a tool and room to change its mind.

The tool and the loop already existed in the codebase from when I built the Converse API layer in [Part 2](https://jamielab.uk/blog/building-the-house-of-knowledge-bedrock-api/): `invoke_with_tools`, five-iteration cap, cumulative token tracking across every round. What didn't exist was a way to run the Post 5 test set through it and score what came back. That was most of the actual work this time: a second eval runner alongside the one from Posts 5 and 6, same golden set, same rubric, agentic path instead of single-shot.

---

## The whole thing in one picture

![Nova Lite versus Haiku 4.5 in agentic mode across the House of Knowledge eval. Three panels: retrieval recall by tier against the Part 6 baseline, both models at 1.00 on lookup, Nova Lite dropping to 0.54 and Haiku rising to 0.76 on synthesis against a 0.60 baseline, temporal at 0.62 baseline versus 0.62 for Nova Lite and 0.71 for Haiku; percentage of queries answered on a single search, Nova Lite 67% (16 of 24) against Haiku 42% (10 of 24); and cost per query against baseline, Nova Lite $0.00011 to $0.00027, Haiku 4.5 $0.00259 to $0.01094.](/images/posts/archivist.png)

That's the whole result before any of the explaining. One model's recall went up once it had the tool, the other's went down, and the reason is sitting in the middle panel: how often each one actually bothered to search twice.

---

## Re-running the test set: it only helps the model that's good enough to use it

| tier | baseline (Part 6) | agentic, Nova Lite | agentic, Haiku 4.5 |
|---|---|---|---|
| lookup | 1.00 recall | 1.00 | 1.00 |
| synthesis | 0.60 recall | 0.54 | 0.76 |
| temporal | 0.62 recall | 0.62 | 0.71 |

Lookup was already solved and stays solved, no surprise there. The interesting split is synthesis. Haiku's recall goes up, meaningfully, from 0.60 to 0.76: letting it search again actually recovers notes a single pass missed. Nova Lite's recall goes *down*, from 0.60 to 0.54. Giving Nova Lite the same tool made it slightly worse at the thing the tool is supposed to help with.

That's not a typo and I checked it twice. The reason is sitting right there in what each model actually chose to search for:

| | Nova Lite | Haiku 4.5 |
|---|---|---|
| mean iterations per query | 2.5 | 2.2 |
| mean search calls per query | 1.5 | 2.1 |
| queries answered on one search | 16 / 24 | 10 / 24 |

Nova Lite takes more turns on average but spends most of them thinking, not searching again, it asks one search question and mostly just sits with the answer. Haiku searches more, and more often follows up a first search with a second, differently-worded one. Handed a tool that lets it reconsider, Nova Lite mostly didn't, and on the minority of queries where its single search wasn't quite right, there was no second attempt to save it. Agentic retrieval isn't a free upgrade you bolt onto any model. It's only as good as the model's judgement about when its first search wasn't good enough yet, and that judgement is exactly the kind of thing that's supposed to separate a cheap model from an expensive one.

---

## The one that went the way I hoped

q11: "How is the House of Knowledge responding to the crisis, and why does Brother Coldis Ren disagree with the Grand Scribe?" Three notes answer it: the House of Knowledge itself, the Grand Scribe, and Brother Coldis Ren. The single-shot baseline got two of three, recall 0.67, missing the institution's own note in favour of a session recap.

Nova Lite searched once, "House of Knowledge response to crisis," and came back worse than the baseline it was meant to improve on: recall 0.33. Its one rephrased query leaned so hard toward the place that it dropped both of the people the question is actually about.

Haiku searched twice. First "House of Knowledge crisis response," much the same idea as Nova Lite's. Then, once it had that, a second search naming the two people the question is actually about: "Brother Coldis Ren Grand Scribe disagreement." That second search is exactly what Part 7 hoped an agent would do: notice a search answered half the question and go get the other half specifically, rather than casting the same net twice. Recall: 1.0, all three notes.

That's the whole case for agentic retrieval in one query. Not "search more." Notice what your first search missed, and go get that specific thing. Haiku did it here. Nova Lite, same query, went the other way entirely.

---

## The one that should have been a clean win, and wasn't

Part 7's k-experiment found something concrete: q24, "how has the plan for Nand's funeral shifted, and why does the timing matter," went from 0.0 recall to 1.0 the moment I asked for ten chunks instead of five. The right note, `2026-03-03.md`, was there all along, just crowded out by `Nand.md` and `Sister Maelin Thorn.md` eating most of the top five between them. More room, free fix, done. If an agent can ask for more chunks whenever it wants, this should have been the easiest win in the whole run.

It wasn't. Both models scored 0.0 recall on q24 in agentic mode. Here's why: Haiku asked for k=10, twice, which on paper should have been exactly the fix Part 7 found. But it didn't search "how has the plan for Nand's funeral shifted, and why does the timing matter", it searched "Nand's funeral plan" and "Nand funeral timing", its own shortened version of the question. Twenty chunks came back across the two calls. Every one of them was `Nand.md`, `Sister Maelin Thorn.md`, `Neverwinter Academy.md`, or the same session recap, repeated. `2026-03-03.md` never showed up, at k=10, twice over. Nova Lite did something similar with its two attempts, "Nand's funeral" and "timing of Nand's funeral," both at the default k=5, and got the identical crowd of the same three notes.

Part 7's fix worked because it changed one variable, k, and left the query exactly as written. The agent changes two variables at once: it picks its own k, and it rewrites the query into something shorter and, it turns out, worse. A bigger net thrown from the wrong spot doesn't catch anything a smaller net from the wrong spot wouldn't. The lesson isn't "agentic search failed here." It's that giving a model the freedom to decide *what* to search for doesn't come bundled with a good instinct for *how* to phrase it, and a worse query can quietly cancel out a wider k before either model notices there's a problem at all.

---

## q23, or: what "try again" actually looks like from two different models

This is the query Part 7 set the whole test up around, and it's the clean contrast the rest of this post doesn't quite deliver.

Nova Lite's full search history for q23, five iterations, five calls:

1. "portable ward device behavior during testing"
2. "portable ward device behavior during testing and reaction to Ultrin"
3. "portable ward device behavior during testing and Ultrin's interaction with it"
4. "portable ward device behavior during testing and Ultrin's interaction with it"
5. "portable ward device behavior during testing and Ultrin's interaction with it"

Three of the five are the literal same string. It hit the iteration cap and produced no answer at all. That's the failure mode Part 7 worried about out loud: an agent that just gives its bad first search another five chunks, dressed up as five separate attempts.

Haiku's search history for the same query:

1. "portable ward device testing"
2. "Ultrin portable ward device"
3. "portable ward device testing behavior"
4. "ward device Ultrin approach reaction"
5. "portable ward sphere artifact"
6. "ward device Ultrin reaction change behavior"
7. "portable ward test approach proximity"
8. "portable ward device testing experiment"

Eight genuinely different angles across five iterations (multiple calls per round, same pattern Nand's-funeral search used). Device, artifact, sphere, proximity, experiment. This is what "search again, differently" is actually supposed to look like, and it's still zero recall. Part 7 already established why: the chunks that share vocabulary with this query are five unrelated 2024 scenes that happen to contain "Ultrin, doing something, something reacting," and no rephrasing that stays inside the same vector space finds its way around that. Haiku's answer, in the end:

> I apologize, but I'm unable to find information about a "portable ward device" and its testing behavior in the campaign notes.

Honest, after real effort. Nova Lite's answer was silence, after less effort dressed up as more. Same corpus gap both times. What differs is entirely what the model does when the first search comes back wrong, which is exactly the axis Part 6 already found between these two models on generation. Turns out it's the same axis on retrieval.

---

## Cost and latency: the bill for all this searching

| model | cost/query: baseline → agentic | latency p50: baseline → agentic | p95 |
|---|---|---|---|
| Nova Lite | $0.00011 → $0.00027 (2.5×) | 642ms → 2375ms (3.7×) | 972ms → 6653ms (6.8×) |
| Haiku 4.5 | $0.00259 → $0.01094 (4.2×) | 2902ms → 6101ms (2.1×) | 4403ms → 11556ms (2.6×) |

Nova Lite's p95 latency got worse, relatively, than Haiku's, which looks backwards until you remember q23: five wasted round trips with nothing to show for it, on the cheap model that's supposed to be the fast one. Haiku's cost multiplier is the bigger number in absolute terms, 4.2 times a baseline that was already 24 times Nova Lite's, but it at least bought something on synthesis recall. Nova Lite's extra spend bought a slightly worse retrieval score and one query that returned nothing at all.

---

## Was there time to score this properly? No, and I'm saying so.

Posts 5 through 7 leaned on blind human scoring as the primary judge, with the automated RAGAS/Mistral faithfulness check running alongside it as a secondary signal, one that agreed with me only 31% of the time and specifically punished honest refusals. This post skipped the human pass. Busy week, and I already knew roughly what the automated judge's failure mode looks like, so I made the call to run judge-only rather than not publish this at all.

I'm not going to pretend that's the same rigor as the last three posts. The faithfulness numbers are in the full report if you want them, and they're about as trustworthy as Part 6 already showed that metric to be, which is to say: a rough signal, not a verdict. One data point that stood out even on those terms: Nova Lite scored *higher* faithfulness than Haiku on lookup and synthesis, which sits oddly next to Haiku's better retrieval recall on synthesis just above. That's either the judge's known bias showing up again, or a genuine finding I don't have the confidence to call from a judge score alone. Filed as unresolved, not smoothed over.

---

## So does the agent fix what Part 7 found?

Sometimes, for one of the two models, on one of the three tiers. That's the honest verdict, and it's a smaller win than I went in expecting.

Haiku's synthesis recall genuinely improved, and that's real: multi-hop questions that need several notes assembled benefit from a model that knows to check again. But q23, the query this whole post was framed around, came back empty from both models regardless of how many honestly different searches one of them tried. q24, which Part 7 had already solved with nothing more than a bigger k, came back broken in agentic mode because the model's own query rewriting undid the fix before the extra budget could help.

Add the cost, roughly triple to quadruple per query, and the latency, two to seven times worse depending on which tail you're looking at, and agentic mode isn't the upgrade the framing of "let the model decide" implies. It's a real improvement for the one failure mode it actually targets, retrieval that's shallow rather than wrong, on the one model with the judgement to use it well. For a coincidental-overlap failure like q23, it's just a slower, more expensive way of not finding the answer. Worth having in the toolkit. Not worth reaching for by default.

---

## What's next

The series started with a local DeepSeek prototype that got replaced by Bedrock because an 8GB NUC couldn't carry generation. Part 9 goes back and asks whether that's still true. A year of small-model progress against pennies-per-query Bedrock pricing, on hardware I actually own rather than hardware I'd need to buy to find out.

I went in hoping for a clean yes. Got "sometimes, if you're paying for Haiku" instead. Part 9 asks a question with a less embarrassing range of answers: does anything on the hardware I already own do this job at all.
