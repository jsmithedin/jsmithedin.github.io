---
title: "Obsidian as a consulting knowledge base"
date: 2026-04-15
tags: [obsidian, consulting, productivity]
description: "How I use Obsidian to manage client context, architecture decisions, and accumulated domain knowledge across engagements."
---

Consulting work has a knowledge management problem. Context is scattered — Confluence pages nobody updates, Slack threads that vanish, Google Docs with version numbers in the filename. Between engagements you lose the thread. Starting a new client in the same domain means rebuilding mental models you've already built.

Obsidian is how I solve this.

## Why not Confluence or Notion

Both are fine for team-shared documentation. Neither is great for personal, fast, evolving knowledge. Confluence has a high-friction editing experience. Notion is flexible but cloud-dependent and slow to navigate by keyboard.

Obsidian is local-first Markdown files. Everything is plain text. It opens instantly. The graph view is useful for spotting gaps. And it works offline on a train from Edinburgh to London, which matters.

## How the vault is structured

```
clients/
  axia/
  jellyfish/
domains/
  energy-storage/
  aws/
  iac/
architecture-decisions/
  ADR-001-multi-cloud-provider-abstraction.md
  ADR-002-sqs-over-batch-for-simulation.md
weekly-reviews/
templates/
```

Client folders are engagement-scoped. Domain folders accumulate knowledge that transfers across clients — BESS dispatch logic, Terraform patterns, IAM gotchas. Architecture Decision Records live at the top level because they're the most valuable artifact to write and the least likely to be written without a home.

## The one habit that makes it work

At the end of every client call or working session, a five-minute note. Not polished — just: what was decided, what's still open, what surprised me. These compound over months. Six months into an engagement you have a searchable record of every technical decision and the reasoning behind it.

The weekly review synthesises these into domain notes. That's where the real knowledge sits.

## Connecting it to the rest of the workflow

The vault is on iCloud for sync across devices. Architecture decisions get copied to Confluence when they need team visibility — manual copy-paste, which is intentional friction: if it's worth sharing it's worth a moment's review.

For D&D campaign notes, the same system works surprisingly well. Sessions are their own vault, enriched automatically via a Claude pipeline that adds recaps and open threads. Same principle: capture fast, synthesise slowly.
