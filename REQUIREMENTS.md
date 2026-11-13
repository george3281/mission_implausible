# Requirements

What the HQ aggregator has to do for "Mission: Implausible 2.0". Source: the
show doc (`Mission Implausible 2.0.docx`, kept outside this repo) and sponsor
feedback. Nothing is built yet. How the AI judges chat and writes cards lives
in `prompt.md`.

## Goal

Turn what the online audience types in the Zoom webinar chat into short,
performable instructions for the actors on stage. The output has to be a real
aggregation of the best ideas in chat, not an echo or paraphrase of individual
messages.

## Setup

- The show runs as a **Zoom webinar**. The audience and HQ are all on Zoom.
- The AI is Claude, with its instructions in `prompt.md`.

## Must do

| # | Requirement |
|---|-------------|
| R1 | Read the Zoom webinar chat live. The capture method is not chosen yet (see `TODO.md`). |
| R2 | Someone on stage starts and stops collecting chat from a simple web app. Stopping sends that round to the AI and shows the 3 selected cards on the same page. |
| R3 | The operator can regenerate a bad set of cards from the same round. |
| R4 | Cards also appear on a display page that updates live, which can be projected or screen-shared into the webinar so viewers see what the AI told the actors. |
| R5 | The AI gets story context: captions of what was said on stage in the last few minutes. |
| R6 | Cards reach the actors in a way they can use mid-scene (stage web app, projector, earpiece, or HQ reading them out). Decide with the director. |

## Constraints

| # | Constraint |
|---|------------|
| C1 | About 30s or less from Stop to cards on screen, so the moment is still happening. |
| C2 | Survives a full performance: reconnects if the chat source drops, and a failed AI call keeps the round so it can be retried. |
| C3 | Show staff can change tone and rules by editing `prompt.md`, without touching code. |
| C4 | Runs on one laptop. |
| C5 | Secrets (API keys, Zoom credentials) are never committed or shown on screen. |
