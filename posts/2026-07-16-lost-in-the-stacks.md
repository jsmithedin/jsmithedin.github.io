---
title: "Building the House of Knowledge: Lost in the Stacks"
date: 2026-07-16
tags: [ai, RAG, House of Knowledge, evaluation]
description: "Part 7 of a series on building a real RAG system with real data. Retrieval scored fine on lookup and fell apart on temporal questions. This is why."
image: /images/posts/stacks.png
---

# Building the House of Knowledge: Lost in the Stacks

*Part 7 of the House of Knowledge series. [Part 1 is here.](https://jamielab.uk/blog/building-the-house-of-knowledge-RAG-on-a-budget/) [Part 6, the model comparison, is here.](https://jamielab.uk/blog/building-the-house-of-knowledge-choosing-your-scholars/)*

---

The last post ended on the one hallucination in forty-eight answers, and the honest read was that it wasn't really about the model. Nova Lite guessed; Haiku hedged. Same missing note, opposite instinct. Underneath both was a retrieval failure: the note that held the answer never made it into the top five.

That's the thread this post pulls all the way out. Every question in this series so far has assumed retrieval works and generation is the interesting part. Post 5 and 6's test set already says otherwise: lookup questions are solved, and the harder tiers aren't. This is what that looks like, and why.

---

## What the test data showed

| tier | avg recall | hit rate |
|---|---|---|
| lookup | 1.00 | 1.00 |
| synthesis | 0.60 | 1.00 |
| temporal | 0.62 | 0.75 |

Lookup is a solved problem: single fact, single note, embeds cleanly, comes back every time. Synthesis is the tier that looks fine until you check the recall column: hit rate 1.00 means every synthesis query got *something* relevant back, but average recall of 0.60 means it's usually missing two out of every five notes an answer needs. It doesn't fail loudly. It fails by handing the model an incomplete case file without saying so, and letting it sound confident about a partial answer.

Temporal is the tier that fails loudly. Hit rate 0.75 means one in four temporal questions came back with nothing relevant at all, not a partial match, nothing. Two of those eight are worth walking through in detail, because they're not the same failure.

---

## A failure taxonomy

Three mechanisms, not one, and the first is doing most of the damage.

**Budget-hogging.** A query needs several notes; one of them embeds closest and eats two or three of the five slots, at the direct expense of the others. This is the synthesis tier's real problem, and it showed up in every partial-recall case I checked. Ask who's competing to lead Neverwinter Academy, a question that names four people, and retrieval hands back the Academy's own note twice (`Key Events` and `Overview`, overlapping content) plus one of the four people, and never gets to the other two. Ask about the plan for Neverdeath Graveyard and one of the two expected session notes takes three of five slots (`Recap`, a scene chunk, `NPCs`) while the other expected session never appears. Ask when Ultrin wounded Nihal and Nihal's own note takes three slots, leaving no room for Ultrin's. It isn't that retrieval misses the topic. It retrieves *too much* of one right answer and crowds out the rest.

**Topically-adjacent, wrong specific note.** The system correctly works out what a question is about and retrieves several genuinely relevant chunks, entity profiles, related people, even the right kind of scene, but not the one specific note with the answer. The Nand's-funeral question below is the clean example.

**Coincidental lexical overlap.** The retrieved chunks aren't wrong for a sensible reason. They just happen to share surface phrasing with the query, entity name plus action verb, while being about something else entirely. The ward-device question below is this one, and it's the least comfortable finding in this post.

---

## Chunking revisited

Post 4 covered structure-aware chunking, splitting each note on its `##`/`###` headings instead of a fixed character count. It's the right call for a wiki of short reference notes. It has a specific failure mode for session logs, and it's easiest to just show it.

Take the session where the ward device test happens, `2026-06-09.md`. It chunks into six pieces: `Recap`, `Open Threads`, `NPCs This Session`, `Items & Loot`, and then two long scene chunks headed `## [[Neverwinter Academy]]` and `## [[House of Knowledge]]`. The ward-device test itself, the whole answer to "how did the device behave when Ultrin approached it", sits inside the `Neverwinter Academy` chunk: forty-odd lines of nested play-by-play, headed with a location name that appears in a couple of dozen other chunks across the vault. There's even a much shorter, denser summary of nearly the same answer sitting in the `Open Threads` chunk for that session: "Portable ward device: bonded to Ultrin, Dean Maverin Soul calibrating for 45 minutes." Neither surfaced. Nothing from this note did. I checked what came back instead, and it's stranger than a heading problem. More on that below.

Where this mechanism does show up clearly is the funeral question and the budget-hogging cases above. Compare `People/Ultrin.md`: it chunks into `Overview`, `Role in the Campaign`, `Key Events`, `Relationships`. Generic headings, every one of them, but the body of each is entirely about one entity. That's a clean embedding target for anything that names Ultrin, and it's exactly why `Nihal.md` and `Neverwinter Academy.md`, both profile-style notes, keep winning the budget-hogging cases above: concentrated, entity-scoped chunks embed more confidently than a scene buried in a session log.

The mechanism, as far as it goes: a session note's chunk is titled by scene or location, which tells the embedding model nothing, because that heading recurs everywhere. An entity note's chunk is titled generically but the body is concentrated. A query that names an entity tends to pull toward that entity's profile note over the session note describing something that happened to them on a specific day. That's real, and it's most of what's going on in the funeral question below. It is not, it turns out, what happened with the ward device question. That one didn't lose to a profile note at all.

---

## The multi-hop problem, or: the eval had its own blind spot

I'd planned this section around q23 and q24 as matched examples of the same failure, both zero-recall temporal questions. Once I had the retrieved chunks in front of me, they turned out not to match at all, and one of them exposed a gap in the eval itself, not just the retrieval system.

**q24**: "How has the plan for Nand's funeral shifted, and why does the timing matter?" Expected note: `2026-03-03.md`, recall 0.0. What actually came back: `Sister Maelin Thorn.md`, `Neverwinter Academy.md`, `Nand.md` twice, and the `Open Threads` chunk from a different session, `2025-12-16.md`. Every single one of those is genuinely about the funeral thread. The system found the topic. It just found the wrong session's version of it.

And look at the question again. "Has shifted" is asking about change over time, and Nand's funeral is a thread that runs through this campaign for two years of game time, mentioned across sessions from early 2024 through mid-2026. The golden set names exactly one of those sessions as the expected source. That's not a fair test of a temporal question. A single note can't tell you how something shifted; you need at least two points to compare, ~~and that's why q24 scored zero~~. Turns out it wasn't why, not quite; skip ahead to the k-bump section, the note was retrievable all along, just crowded out. The golden-set critique still stands as a design flaw worth naming, it just isn't the explanation for this particular failure.

I wrote the golden set in Post 5 specifically to stop myself grading my own homework generously, and it still let a single-note answer stand in for a question that structurally needs more than one. Worth naming plainly rather than fixing it and moving on: the eval methodology has its own version of the retrieval problem, expecting one answer to a question that's actually asking about change. I've left it as-is rather than patching the golden set after the fact; re-baselining one query after seeing the result would be grading my own homework in the other direction.

**q23**: "How did the portable ward device behave during testing, and what changed when Ultrin approached it?" Same shape of question, same zero recall, completely different failure. What came back: five chunks from old 2024 session notes, "Headed to Raven's nest," a manor scene, another manor scene, a residential scene, and a Farm Realm chunk. None of them are about the ward device. None of them are even from the right year.

I went and read the text behind all five hits, expecting one lucky coincidence and four weaker echoes. Instead all five follow the same pattern, and one of them is closer than I expected. The top hit is a scene about renting a storage unit at a warehouse, and it has Ultrin doing things in it: "Ultrin casts suggestion," "plus Ultrin head inside." Another, from a different 2024 session at Veilgard Manor, has Ultrin talking about dreams and defences, and includes the line "Ultrin knows of protective wards that could protect against the dream." Protective wards. Not the portable ward device, but close enough in wording that I'd believe an embedding model blurs the two. A third hit, a profile chunk for a place called the Farm Realm, describes creatures that "turned to look directly at him" when Ultrin did something, which is structurally almost the same shape as "what changed when Ultrin approached it." None of these five chunks are about the ward device. All five share vocabulary or sentence shape with the query in a way that has nothing to do with the answer. The embedding isn't wrong to think these are similar to the query. It's matching on "Ultrin, doing something, something reacting", and that pattern shows up constantly across two years of session notes, almost none of it about this one device.

That's a different kind of failure to q24. q24 found the right topic and the wrong timepoint, and turns out to be fixable by asking for more chunks. q23 didn't find the topic at all; it found a coincidence, and no amount of asking for more chunks fixes that (confirmed below). With 247 notes and a small recurring cast, "mentions the same proper noun in an active sentence" turns out to be enough surface similarity to beat genuine relevance outright.

---

## Does a bigger k fix it?

Ran it. Same as Post 6: the plan didn't survive the data.

| tier | k=5 recall | k=10 recall | k=15 recall |
|---|---|---|---|
| lookup | 1.00 | 1.00 | 1.00 |
| synthesis | 0.60 | 0.85 | 0.85 |
| temporal | 0.62 | 0.81 | 0.88 |

The headline number looks like a clean win: synthesis jumps 25 points just by asking for twice as many chunks, temporal keeps climbing all the way to k=15. Doubling k for free (this is pure retrieval, no extra Bedrock spend) buys a real improvement. But the per-query breakdown is where it gets interesting, and where my own predictions in this section, written before I ran it, mostly missed.

**Budget-hogging queries mostly fixed at k=10, exactly as predicted.** q09 (0.50 → 1.00), q10 (0.50 → 1.00), q11 (0.67 → 1.00), q14 (0.67 → 1.00) all resolve cleanly the moment there's enough room for the dominant note and the starved one to coexist. That part of the theory held.

**q24 got fixed. I said it wouldn't.** I'd predicted a wider net would just pull in more of the wrong session's chunks, since the failure looked like "correct topic, wrong timepoint" rather than "correct note, ranked too low". Recall went from 0.0 to 1.0 at k=10. Turns out `2026-03-03.md` was in the similarity neighbourhood all along, just outside the top five, competing with the same entity-profile chunks that beat it there. That's budget-hogging too. I'd assumed a wrong timepoint meant the note was genuinely absent. It wasn't, just crowded out. Worth sitting with: my "topically-adjacent, wrong note" category and my "budget-hogging" category turned out to be the same mechanism wearing two descriptions, and only the k experiment told them apart.

**q23 didn't move. I said it wouldn't, and this time I was right.** Recall stayed at 0.0 through k=15. The coincidental-overlap chunks aren't ranked sixth or tenth waiting to be let in with a wider net, they're winning outright, and the right answer isn't competitive at any depth I tested. This is the one mechanism a bigger k can't touch, because the problem isn't depth, it's that the ranking itself is wrong for this query.

**q12 and q13 also didn't move, and I don't have a clean explanation for these two.** Both flat across all three k values (0.67 and 0.50). Neither fits the coincidental-overlap story the way q23 does, nothing in their retrieved chunks looks like an unrelated coincidence, but neither fits the budget-hogging story either, since more room didn't help. Leaving this as an honest gap rather than forcing an explanation: something about these two queries' missing notes puts them further outside the similarity neighbourhood than q24's was, and I haven't dug into why. If Post 8's agent also fails on these two, that's a useful data point in itself.

**q21 needed k=15, not k=10** (0.50 → 0.50 → 1.00). A milder version of the same story as q24: the starved note was there, just further down than the others.

**q15 only half-fixed, and stays there** (0.33 → 0.67 → 0.67). This one needs three notes, and even at k=15 only two of them ever show up. One extra slot of room recovered one missing note; it didn't buy the third. Budget-hogging is real here, it's just not fully solvable by depth alone when a query needs enough different notes.

So: a bigger k is a real, free, honest fix for most of the budget-hogging failures, including one I'd wrongly filed under a different category, though not always a complete one. It buys nothing at all against genuine coincidental overlap. And two queries sit in a category I can't yet name.

---

## Other mitigations, priced honestly

Hybrid search (BM25 keyword matching alongside the vector search) and re-ranking a wider candidate set with a second, cheaper model are both real options, and neither exists in this codebase yet. Building and testing them properly is its own piece of work, not an afternoon's addition to this post. Naming them without pretending I've tried them: hybrid search is the one I'd bet on for q23 specifically. "Ward device" and "portable ward" are exact, unusual terms that appear almost nowhere else in the corpus; a keyword search would nail the right chunk regardless of what the vector similarity thinks about Ultrin-plus-verb phrasing. Re-ranking is really just a smarter version of what the k-bump experiment already showed works: if the starved note is somewhere in a wider candidate pool, promoting it does the same job the bigger k did for q09/q10/q11/q14/q21/q24, probably more cheaply than retrieving fifteen full chunks on every query. Neither one obviously touches q23, since re-ranking still starts from the same candidate pool a wider k pulls from, and that pool doesn't contain the right answer at any depth I tested.

Metadata filtering, letting a query scope itself to an arc, session, or tag, already exists in the app. It needs the user or the model to already know which session or arc to scope to, though. That's not a retrieval fix, it's a UI feature for someone who already half-remembers the answer.

---

## What a bigger k can't buy

Most of what looked like a deep, structural retrieval problem turned out to be a capacity problem with a free fix: ask for more chunks. That's most of the synthesis tier and half the temporal failures, including one, q24, I'd wrongly diagnosed as something more interesting than it was.

Two failures stayed broken no matter how wide the net went. q23, where the right answer isn't in the similarity neighbourhood at any depth I tested, because the query and the right chunk just don't share enough vocabulary, while several wrong chunks share plenty. And q12/q13, which fail the same way at every k for reasons I haven't pinned down yet. Both of those need the system to notice a search came back thin or wrong, and try a different, more specific query instead of trusting the first match. That's a *decide what to search for next* problem, not a *look further down the list* problem, and it's exactly the difference between one retrieval pass and an agent that can search again. Whether an agent actually closes that gap, rather than just giving the same bad first search another five chunks, is the open question Post 8 has to answer.

---

## What's next

Part 8 asks the obvious follow-up: if the model can run its own searches instead of taking one shot, does it fix what a bigger k couldn't? Specifically q23, does it know to search "2026-06-09 ward device" as a second, narrower query when the first, broader one comes back full of confident nonsense? And q12/q13, which I still can't explain, will be a useful test in themselves: if an agent fixes them too, that's a clue about what was wrong. I have a guess about how this goes. I've already been wrong once in this very post, so I'm not writing the verdict until I've run it.

---
