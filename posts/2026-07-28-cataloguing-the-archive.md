---
title: "Building the House of Knowledge: Cataloguing the Archive"
date: 2026-07-28
tags: [ai, RAG, House of Knowledge, evaluation]
description: "Part 9 of a series on building a real RAG system with real data. Google published a spec for the wiki-of-markdown-files pattern this project already used by accident. Testing whether the one thing it adds actually fixes anything."
image: /images/posts/cataloguing-the-archive.png
---

# Building the House of Knowledge: Cataloguing the Archive

*Part 9 of the House of Knowledge series. [Part 1 is here.](https://jamielab.uk/blog/building-the-house-of-knowledge-RAG-on-a-budget/) [Part 7, where retrieval fails, is here.](https://jamielab.uk/blog/lost-in-the-stacks/) [Part 8, the agentic follow-up, is here.](https://jamielab.uk/blog/the-thinking-archivist/)*

---

The vault behind this whole series wasn't built for retrieval. It's session notes, NPC write-ups, and place descriptions for a D&D campaign, written the way you'd write anything in Obsidian: `[[wikilinks]]` between the things that reference each other, because that's how you find your own notes again, not because anyone was thinking about a RAG pipeline. The RAG system got bolted on top of that afterwards, back in Part 1.

Which is why the Open Knowledge Format caught my eye. Google Cloud published it on the 12th of June: a spec for structuring exactly this kind of thing, a directory of markdown files with typed frontmatter, cross-linked into a graph. My vault already looked like that, minus the labels. So the question isn't "should you adopt OKF," which is the framing every hot take has gone with. It's narrower: I've already got a working RAG system built on this vault. Does adding OKF's structure on top of it, the types and the graph, actually make retrieval better?

There's also unfinished business worth naming properly rather than by query number. Part 7 left two synthesis questions that no depth of vector search ever fixed: one asking what the party actually knows about a recurring villain and the plague tied to him, the other about their history with a graveyard that came up across two separate sessions. Part 8's agent didn't crack either; it went chasing a different failure instead, a question about a ward device where the same wrong chunks kept surfacing no matter how many times it re-searched. Three posts in, still open. I had a real prediction about whether OKF would close any of that. I was mostly wrong, in an interesting way.

---

## What OKF actually is, and what was already sitting on disk

The whole spec fits on one page, deliberately. A bundle is a directory of markdown files. Each file is a concept, a table, a person, a runbook, whatever you're describing. Each concept gets a small YAML frontmatter block: `type`, `title`, `description`, `resource`, `tags`, `timestamp`. Only `type` is required. Concepts link to each other with ordinary markdown links, and those links form a graph, richer than the folder structure alone implies. That's it. No SDK, no runtime, no registry. Andrej Karpathy called the underlying pattern the "LLM wiki" back in April; Google's contribution is agreeing on the handful of field names so different tools can read the same bundle without a translation layer.

Every note in the vault already had `title` and `tags` in its frontmatter, long before any of this started, because that's what makes an Obsidian vault worth using: you tag things and link them so you can find your own notes again six months later. The folders (People, Places, Sessions, Organisations, Monsters, Bad Guys, Props, OneShots) already map onto OKF's idea of typed concepts. The notes already link to each other, four thousand times over, for the same reason, not because anyone was thinking about retrieval. It's just what two years of actually using Obsidian looks like, put together before the RAG system existed, let alone the spec that would eventually put a name to the pattern. I already had a natural experiment sitting on disk.

What's actually missing is small and specific. No `type` field anywhere. And the links, real as they are, only ever get read by Obsidian's own renderer. The retrieval side of this project splits each note into sections and embeds them for search; it never once looks at a link between notes. The wikilinks are decoration as far as retrieval's concerned.

---

## Building a producer

Turning the vault into an OKF bundle meant a script that does four things to every note: walk the vault, assign a `type` from the folder name, add a description and a timestamp, and turn the existing links into the plain markdown links OKF actually wants. Converting 288 notes took an afternoon. Most of that afternoon went on the links, not the frontmatter.

Folder to type was a flat lookup, nothing clever:

| Folder | `type` | Count |
|---|---|---|
| People | Person | 88 |
| Places | Place | 67 |
| Sessions | Session Log | 40 |
| Bad Guys | Antagonist | 39 |
| Organisations | Organisation | 31 |
| Monsters | Monster | 15 |
| (top-level, no folder) | Note | 4 |
| OneShots | One-Shot | 2 |
| Props | Item | 2 |

The links were the real work. Four thousand of them in the vault, and only ninety percent resolved to an actual note on the first pass. The rest split evenly between two problems, neither one caused by the conversion itself. Some links were already dead: `Marka the Dead` gets referred to as just `Marka` nine times in her own note, and no `Marka` note or alias ever existed to catch it, so those references were broken in Obsidian long before I touched anything. Others were ambiguous rather than missing: `Baphomet`, `Duanaogar the Defier`, and a few more each exist as two separate notes, once under People and once under Bad Guys, most likely a villain reclassified at some point without the original getting deleted. Obsidian never surfaces either problem, grey unclickable text and two same-named files in different folders don't collide in its view. Converting to OKF forces a single answer for every link, so both got written down in a report instead.

One actual bug turned up here: a handful of image embeds and one note transclusion use a different bracket syntax, meant to insert content rather than just point at it. The first version of the script didn't know the difference and quietly turned a working embed into a broken image link. Fixed by leaving that syntax alone.

---

## Building a consumer

It's worth being clear up front: none of this replaces ChromaDB. The same BGE-M3/Chroma setup from Part 1 still does the actual search, embedding the query, finding the closest chunks. OKF doesn't touch that step. What it adds sits after it.

Vector search finds the five notes that seem closest to the question. Graph-walk starts from those same five, then also pulls in whatever those five link out to, one step further, on the theory that a missing note is often sitting one click away from something that was already found. If a question needs three notes and vector search only surfaced two of them, the third might be reachable by just following a link from one of the two.

The obvious way to test this badly is to compare graph-walk against plain search at the same starting point, five notes against five notes plus their neighbours, and call it a win when the version with more notes does better. That's not a result, it's just giving one side more to work with. Part 7 already proved more context helps; that's the entire k-experiment. So the real comparison here is graph-walk against vector search at ten or fifteen notes, roughly the same amount of material, two different ways of choosing what's in it.

Two things went wrong before I got anywhere near real numbers, both found by running the mechanism against the actual converted vault rather than assuming it would behave the way I expected.

**First: a link only runs one way.** q12 needs `Places/Neverdeath Graveyard.md` plus two session logs. I checked what the graveyard's own note links to: Neverwinter, the Raven Queen, Lord Neverember. Never a session. Then I checked the sessions themselves: both link to the graveyard, because that's where the scene happened. A session note writes down where the party went. The place's own note never writes down which sessions mentioned it. So starting from the graveyard and following its links outward finds more places and people, never the session where the party actually stood in it. Fixed by treating every link as running both ways, the same thing Obsidian's own backlinks pane already does for you without you noticing.

**Second, and it showed up the moment the first was fixed: some notes get mentioned constantly, across sessions that have nothing to do with each other.** `Neverdeath Graveyard.md` is one of them. Once links run both ways, following them out from just two starting notes reached 267 of the vault's 288 notes. That's not a missing note turning up one step away. That's most of the vault, relabelled, which would win on recall for the dumbest possible reason: it isn't really a smaller, targeted set any more. So the walk gets capped, stopped once it's pulled in as many notes as vector search at fifteen would have anyway, so neither side wins just by having more material to work with.

---

## The test, and the result I didn't expect

Same 24-query golden set from Part 5, reused for the fifth time now, split into the same three tiers: lookup (one fact, one note), synthesis (the answer needs combining more than one note), and temporal (how something changed over time). Same scoring too: recall, the fraction of the notes a question actually needs that the method actually found. Four conditions across the columns: vector search at k=5, 10, and 15, and graph-walk built from k=5's results plus one capped hop. Each cell reads as recall, then the average number of notes it took to get there, because a method winning just by retrieving more isn't a result worth having.

| tier | vector k=5 | vector k=10 | vector k=15 | graph-walk (cap 15) |
|---|---|---|---|---|
| lookup | 1.00 / 3.4 notes | 1.00 / 6.4 | 1.00 / 8.2 | 1.00 / 14.1 |
| synthesis | 0.60 / 3.2 | 0.85 / 6.9 | 0.85 / 10 | 0.81 / 15 |
| temporal | 0.62 / 3.9 | 0.81 / 6.2 | 0.88 / 9.8 | 0.81 / 15 |

Look at the synthesis row. Graph-walk beats k=5, the set it's built from, 0.60 to 0.81. It never catches k=15's 0.85. And it does this while burning its entire 15-note budget on almost every query, where k=15 gets a better result on an average of 10 notes. That's the headline, and it's not the one I went in expecting: **the graph doesn't beat deeper vector search, and when it loses, it loses at an equal or larger cost.**

The per-query numbers matter more than the averages above, sorted by query number with what each one turned out to be a case of:

| query | tier | k=5 | k=10 | k=15 | graph-walk | case |
|---|---|---|---|---|---|---|
| q09 | synthesis | 0.50 | 1.00 | 1.00 | 0.50 | regression |
| q10 | synthesis | 0.50 | 1.00 | 1.00 | 1.00 | matched by k |
| q11 | synthesis | 0.67 | 1.00 | 1.00 | 1.00 | matched by k |
| q12 | synthesis | 0.67 | 0.67 | 0.67 | 0.67 | unmoved |
| q13 | synthesis | 0.50 | 0.50 | 0.50 | **1.00** | graph win |
| q14 | synthesis | 0.67 | 1.00 | 1.00 | 1.00 | matched by k |
| q15 | synthesis | 0.33 | 0.67 | 0.67 | 0.33 | regression |
| q18 | temporal | 0.50 | 1.00 | 1.00 | 0.50 | regression |
| q21 | temporal | 0.50 | 0.50 | 1.00 | 1.00 | matched by k |
| q23 | temporal | 0.00 | 0.00 | 0.00 | 0.00 | control |
| q24 | temporal | 0.00 | 1.00 | 1.00 | 1.00 | matched by k |

**q13 is the clean win, and it's the one that justifies the whole exercise.** "What does the party know about Kyusse and the plague in Neverwinter?" needs `Bad Guys/Kyusse.md` and `Places/House of Knowledge.md`. Vector search never finds both, not even at k=15, it's stuck at 0.50 through every budget I gave it. Graph-walk gets it every time, because those two notes link to each other directly, and no amount of semantic similarity search ever put them in the same top-15 together. That's a real, structural relationship that embeddings genuinely can't see, and a link genuinely can.

Five more, q10, q11, q14, q21, q24, are budget-hogging cases Part 7 already fixed with a bigger k. Graph-walk matches those fixes without beating them, which is fine, not the interesting part, just worth showing rather than hiding behind an average.

**q09, q15, and q18 are the honest cost of that win.** Deeper vector search fixes all three; graph-walk doesn't move any of them. In each case the missing note apparently isn't one hop from whatever k=5 found, so there's nothing for the walk to reach, while a wider vector search finds it some other way, embedding similarity alone, no link required. Neither method subsumes the other. They're catching different misses, and sometimes the plain one wins.

**q12 stays at exactly 0.67, everywhere, under every method I've now thrown at it across three posts.** k didn't move it. The agent didn't move it. The graph didn't move it. I don't have an explanation, and I've stopped expecting to find one.

**q23 stayed at zero, exactly as I predicted going in, and that's the one prediction that held.** The wrong chunks retrieved for the ward-device query were never linked to the right one, because there's no real relationship there to link, just coincidental phrasing. A graph edge can't invent a connection that doesn't exist in the source material. Structure fixes structural misses. It was never going to fix a ranking problem.

---

## Does the converted vault still work as a vault?

Worth asking directly, because the answer isn't "who cares, it's just an experiment." I checked, and confirmed it two ways.

Quartz, which builds the actual published wiki, turned out fine by reading its own source rather than guessing. `ObsidianFlavoredMarkdown` converts `[[wikilinks]]` into plain HTML links before Quartz's own link-crawler ever runs, and that crawler builds backlinks and the graph view from whatever `<a href>` survives, regardless of which syntax it started as. The vault-root-relative paths my script writes resolve the same way Quartz's own "absolute from vault root" option already does. Backlinks, graph view, everything, identical either way.

Obsidian itself I opened the converted bundle in directly, and it works as a vault. Which is how I found the embed bug above in the first place, because a broken image is the kind of thing you only notice by actually opening the file, not by reading a conversion report.

Given that, the honest framing isn't "migrate the vault to OKF." It's a build step, the exact same relationship Quartz already has to the source markdown: one format produced from another, nobody hand-edits the output. I keep writing in Obsidian with wikilinks exactly as before. The conversion runs before indexing, feeding the experiment, not replacing anything.

Small, unrelated aside worth naming for anyone tempted to go further than I did: there's already a five-day-old Obsidian plugin, OKF Enforcer, that validates and auto-fixes this stuff live in the editor, missing `type` fields, `index.md` generation, the works. 57 downloads at time of writing. I'm apparently not the only one who read the same Google Cloud blog post and had the same idea within a week.

---

## So was it worth building

Yes, and the case for it is simpler than the recall table alone makes it look. The conversion script and the graph-walk consumer are a few hundred lines and an afternoon each, on top of frontmatter and links a well-kept vault already has for other reasons. That's not a research budget. It's an afternoon.

For that, it caught q13 outright: a real relationship between two notes that vector search never found at any k I tested, recovered because those two notes happen to link to each other. Three posts of trying, a bigger k, a second model, an agent free to search again, none of it found that. A link did.

q09, q15, and q18, where graph-walk falls behind deeper vector search, aren't really a cost of having the graph. They're a reminder that it's a second way of finding notes, not a replacement for the first. Nothing stops you running both and keeping the union: vector search at whatever k you already use, plus a capped hop on top. The graph only has to add what vector search missed, not beat it outright, and on that basis it's hard to see a reason not to add it once the frontmatter's already sitting there.

q12 and q23 are the honest limit rather than the cost. q12 hasn't moved under anything I've thrown at it across three posts, and q23 never had a real relationship for a link to recover in the first place. A cross-link graph fixes one specific kind of miss: two things genuinely connected but never phrased alike enough for embeddings to notice. It was never going to fix the ones that aren't that.

Worth mentioning too: converting the vault surfaced 376 already-broken links and a handful of duplicated entities I didn't know about, free of charge. Not the point of the exercise, but a reasonable bonus for an afternoon's work.

---

## What's next

Part 1 started with a local DeepSeek prototype that got replaced by Bedrock because an 8GB NUC couldn't carry generation. Part 10 goes back and asks whether that's still true a year on, given how far small models have moved and how little Bedrock actually costs per query. I already know the answer isn't going to be a clean yes. It wasn't a clean yes for the agent in Part 8, or the graph in this one. Consistent, if nothing else.
