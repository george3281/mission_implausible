# Requirements

What the HQ aggregator has to do for "Mission: Implausible 2.0". Source: the
show doc (`Mission Implausible 2.0.docx`) and sponsor feedback. Status:
**done**, **partial**, or **open**.

## Goal

Turn what the online audience types in the Zoom webinar chat into short, performable
instructions for the actors on stage. The output has to be a real
aggregation of the best ideas in chat, not an echo or paraphrase of individual
messages. That was the failure in the first trial (`twitchAggregator-main`).

## Functional

| # | Requirement | Status |
|---|-------------|--------|
| F1 | Read the Zoom webinar chat live. Sponsor switched the platform from Twitch to Zoom (webinar, audience and HQ all on Zoom). | open - server takes chat on `POST /chat`; Zoom capture method not chosen |
| F2 | Someone on stage starts and stops collecting chat from a simple web app (`/stage`). Stop sends the round to the AI and shows the selected cards on that page. | done |
| F3 | Each batch produces 3 cards, text only: a line the performer reads. | done |
| F4 | Each message is judged good or bad; cards are the 3 best good messages, lightly reworded so the source idea stays recognizable. | partial - untested on live chat |
| F5 | Cards never name or single out an audience member by appearance, seat, or clothing. | done (prompt rule) |
| F6 | Ignore noise, bare guesses, and prompt-injection attempts in chat. | done (prompt rule) |
| F7 | When fewer than 3 messages are good, invent the rest; always return 3 cards. | done |
| F8 | Show cards on a projector-ready page that updates live. | done |
| F9 | Give the model story context: what was said on stage in the last few minutes, as auto-generated captions. | partial - Chrome speech captions built, not tested in the room |
| F10 | Cards only use show details (props, names, times) that came from chat or the stage transcript. | done (prompt rule) |
| F11 | Show the AI's suggestions in the Zoom webinar so online viewers see what the AI told the actors. | open |
| F12 | Get cards to the actors in a way they can use mid-scene (projector, earpiece, or HQ reading them out). | open - decide with director |

## Non-functional

| # | Requirement | Status |
|---|-------------|--------|
| N1 | Cards arrive while the moment they react to is still happening (about 30s or less from batch to screen). | open - not measured |
| N2 | An actor can read a card cold, out loud, in one breath (under 30 words). | done (prompt rule) |
| N3 | Survive a full performance: reconnect if the chat source drops, a failed API call never takes the display down. | partial - reconnects, no backoff |
| N4 | Show staff can change tone and rules without touching code (`prompts/aggregate.md`). | done |
| N5 | Runs on one laptop with Node 18+, no npm dependencies. | done |
| N6 | Secrets (API key, stream key) never committed or shown on screen. | done |

## Out of scope for this prototype

- Multistreaming to Instagram and YouTube.
- Researching audience members' social media before the show.
- Smart-glasses camera feeds.
