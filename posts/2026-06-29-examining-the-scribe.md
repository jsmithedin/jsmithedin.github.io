---
title: "Examining the Scribe: Building a Test Set That Doesn't Lie"
date: 2026-06-29
tags: [ai, RAG, House of Knowledge, evaluation]
description: "Part 5 of a series on building a real RAG system with real data - building an evaluation set honest enough to compare two models without fooling myself."
image: /images/posts/scoring.png
---

# Examining the Scribe: Building a Test Set That Doesn't Lie

*Part 5 of the House of Knowledge series. [Part 1 is here.](https://jamielab.uk/blog/building-the-house-of-knowledge-RAG-on-a-budget/)*

---

The next post in this series was meant to be the fun one. Two models, Nova Lite and Haiku 4.5, same RAG pipeline, same questions, and a verdict on which one to keep. I had it half-written in my head. Ask a dozen questions, read the answers, pick the better set.

Then I noticed who was doing the picking.

I didn't write the campaign and I don't keep the notes; another player does. But I play in it, I wrote the test questions, I wrote the expected answers, and I pay the Bedrock bill. And I have a favourite, because Nova Lite is around sixteen times cheaper than Haiku and I am, as established across four previous posts, tight. Most of those facts pull in the same direction. "Looks right to me" was never going to be a fair test. It was going to be me marking my own homework with the answers already written in the margin.

So this post is the one I didn't plan to write. No results, no winner. Just the work of building something that can tell me I'm wrong.

---

## The problem with vibes

Evaluating a RAG system by reading a few answers and nodding feels fine right up until you write down what you're actually doing. You are asking one biased person to judge unlabelled output against a standard that only exists in their head, on a sample they chose, for a system they built. None of those steps is neutral.

The fix isn't complicated, but it is work. You need questions written down in advance, expected answers written before any model runs, and a scoring process that doesn't know which model produced what. None of that is clever. It's just discipline, and discipline is the part you're tempted to skip when it's a hobby project and nobody's watching.

I hadn't done this kind of testing myself. I've been around it at work, where the AI specialists talk about eval sets and judges and agreement rates, but listening to it being discussed and actually doing it are different things. So before building anything I went and read how the field does it properly.

---

## How it's actually done

The consistent message across the literature is to evaluate retrieval and generation separately. A bad answer has two possible causes. The right notes never surfaced, or they surfaced and the model made a mess of them. If you only score the final answer you can't tell which, and the two problems have completely different fixes. One is a retrieval bug, the other is a model choice.

Retrieval scoring turns out to be the easy half, because it doesn't need a judge at all. For each question you list the notes the answer actually lives in, then check whether chunks from those notes show up in the top results. [Evidently's guide to RAG evaluation](https://www.evidentlyai.com/llm-guide/rag-evaluation) dresses this up as context recall and context precision, but at my scale it reduces to a blunt question with a yes or no answer. Did the right note come back or not? That's a Python loop, not a framework.

Generation scoring is the hard half, because judging whether an answer is correct and complete needs something that understands the words. That something is either a human or another model, and both come with problems.

The bit I underestimated was the golden dataset. A set of question, expected answer, and source notes, all written and verified before any model runs. Every source I read flagged it as the step people skip, and there's no automated shortcut. For my project that's fine. I play in the campaign, so I know it well enough to write the ground truth. The only rule that matters is writing the expected answer first, because the moment you see the model's output it becomes the anchor and your "expected" answer quietly bends to match it.

---

## Building the test set

I settled on 24 questions across three tiers, eight in each.

The first tier is lookup: a single fact in a single note. "How many healing potions can the Academy supply each night?" The second is synthesis, where the answer has to be assembled from several notes. "What are the three factions competing to lead the Academy, and what does each want?" The third is temporal, which is the interesting one for a campaign that's run for years. "How has the Academy changed since Nand died?" That last kind is where a wiki search falls down and a decent RAG system should earn its keep.

Two things came out of building it.

The first is mundane but it matters: you have to freeze the corpus before you test against it. The House of Knowledge only indexes notes that carry YAML frontmatter and headings to chunk on. There are 247 of those today, up from the 87 I started the series with, because I've kept adding sessions and fleshing out the notes as the campaign has gone on. That's the system getting better, which is the entire point. It's also a moving target, and a moving target is useless for a test. So step zero is to pin the corpus at a fixed version and leave it alone until the run is finished. Change the notes, change the index, and the numbers stop being comparable.

The second was sharper: whether my questions actually tested anything. My first batch of lookups were all of the form "who is X", where X was the exact title of a note. They looked like a test. They weren't. When the question names the note, the retrieval is trivial, the right chunk comes back basically every time, and the recall score is a flat pass regardless of how good or bad retrieval really is. I'd have got a row of green ticks and learned nothing.

So I rewrote half of them to hide the target. "Who died defending two unmarked graves at the estate?" The answer is a servant called Edgar, but the question never says his name, so the system has to actually retrieve on meaning rather than match a title. That single change is the difference between a test that flatters the system and one that can fail it. Catching it before the run, rather than after, is the whole reason this post exists.

---

## The judge problem

For the generation side, using one model to judge another's answers is now the standard move at scale. The headline finding is encouraging: a good judge agrees with human reviewers about [85% of the time](https://www.confident-ai.com/blog/why-llm-as-a-judge-is-the-best-llm-evaluation-method), which is better than two humans agree with each other. Then you read the next paragraph and the encouragement drains away.

LLM judges have biases, and they're well documented. There's position bias, where the judge prefers whichever answer it sees first, to the tune of about ten percent. There's verbosity bias, where the longer answer scores higher even when the shorter one is more correct, because length reads as effort. And there's [self-preference bias](https://arxiv.org/abs/2410.21819), where a model rates its own output more highly, also around ten percent, apparently because it likes text that resembles its own style.

That last one matters for my setup. The honest mitigation is to use a judge from a different model family than the contestants, so it can't quietly prefer its own work. My contestants are Nova Lite, from Amazon, and Haiku, from Anthropic, so the judge needs to be neither.

Mistral Large fits. It's in neither family, so self-preference doesn't apply. It's available in the same London region the rest of the project runs in, and it's the cheapest of the neutral options. A faithfulness check, which is all I'm asking the judge to do (is every claim in this answer supported by the retrieved notes), is the least demanding kind of judging, well inside what Mistral Large handles. So the judge isn't a contestant wearing a disguise, and it isn't a line on the bill worth worrying about.

But settling the judge raised a bigger question: why am I leaning on it at all?

---

## The interesting inversion

In a production setup you run automated metrics on everything and have a human review a sample. The human is the expensive bit you ration.

At my scale the maths flips. Twenty-four questions times two models is forty-eight answers. Add the blind scoring and that's an evening with a beer. The "sample" is the entire set, so there's no reason to ration the human at all. And for this corpus the human is the better judge anyway, by a distance. No model on earth has sat at the table for years of this campaign. I have.

So the roles swap. The human is the primary judge, and the LLM judge becomes the experiment. I run it in parallel, on faithfulness only, which is the one thing it can check without domain knowledge, and then I measure how often it agrees with me. That agreement rate is the actual finding. If it's high, later posts in this series can lean on automated scoring and I'm not hand-marking answers forever. If it's low, I am. Either way it's a number worth publishing, and I won't know which until I run it.

The scoring itself is deliberately awkward to game. A script strips the model names, shuffles the order, and labels the answers A and B. I score them one at a time against a rubric, correctness out of two, completeness out of two, and a hallucination flag, with no idea which model I'm looking at. The unmasking is a separate step I don't run until every answer is scored. The point is to make it hard for me to do the thing I most want to do, which is let Nova Lite off lightly because I want it to win.

---

## The tools, briefly

I looked at the obvious frameworks. [RAGAS](https://docs.ragas.io/) is the RAG-specific standard and has proper implementations of the judge metrics, so it's doing the faithfulness scoring. [promptfoo](https://www.promptfoo.dev/docs/providers/aws-bedrock/) is good, but it wants to own the model calls, and my pipeline has custom retrieval bolted into the middle that it would have to be talked around. By the time you've done that you've written the harness anyway, so I noted it and moved on. DeepEval is built for CI regression, which isn't what a one-off comparison needs.

What's left is mostly my own code. The harness is about a hundred lines looping the questions over the existing pipeline and writing the results out. RAGAS handles the judge layer. The blind-scoring page is Streamlit, which the project already uses, so it costs me nothing new. Every framework would have needed me to write that harness regardless. Sometimes the boring answer is the right one.

The whole run, both models across all the questions plus the judge calls, will cost comfortably under a pound. The expensive part was never the compute. It was being honest about the result.

---

## What's next

The harness is built. The golden set is written and the expected answers are locked in before a single model has run, which was the entire discipline I set out to keep. The next step is to actually run it, score the answers blind, and see what the report says.

So Part 6 is finally the comparison I meant to write weeks ago. Nova Lite against Haiku, on a test set designed to stop me handing the result to the one I'm backing.

I genuinely don't know who wins yet. That's the first time in this whole project I've been able to say that and mean it.

---
