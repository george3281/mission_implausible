# TODO

Requirement numbers refer to `REQUIREMENTS.md`.

## Decide first

- [ ] Pick how Zoom webinar chat gets captured (R1). Options:
  - **Event subscription over WebSocket or webhook** (`webinar.chat_message_sent`, via a Server-to-Server OAuth app). No public URL is needed with WebSocket. Dev forum reports (2025-2026) say it often never fires, may need Zoom Support to enable In-Meeting Chat DLP, and may only fire for users inside the app owner's account. Webinar attendees are outside the account.
  - **Browser script** in HQ's Zoom web client that reads chat from the page. No Zoom app needed, but it breaks when Zoom changes the page, and Zoom's CSP may block sending to localhost.
  - **RTMS (Realtime Media Streams)**. Includes transcripts. Sources disagree on whether it includes chat.
  - **Bot** (Zoom Meeting SDK or Recall.ai). Most reliable, but the most work or money.
- [ ] Run the 15-minute test: on the sponsor's Zoom account, create a Server-to-Server OAuth app with the `webinar:read:chat_message:admin` scope and a WebSocket event subscription for "Webinar chat message sent". Then send a chat from an attendee on a **different** account and check whether the event arrives.
- [ ] Confirm the sponsor has a Zoom Webinars license.
- [ ] Confirm webinar settings: attendee chat is on (not Q&A only), and who attendees can chat with.
- [ ] Decide with the director how cards reach the actors: the stage web app, projector, HQ reading them out, or an earpiece. (R6)

## Build

- [ ] Stage web app: Start/Stop button, message count while collecting, the 3 cards after Stop. Pressing Stop again regenerates. (R2, R3)
- [ ] Projector / screen-share display that updates on every Stop. (R4)
- [ ] Stage captions for story context. Chrome speech recognition is the cheapest option. Zoom's own transcripts are another option if RTMS is used. (R5)

## Prompt

- [ ] Run a set of sample chats through the prompt with and without a sample stage transcript and compare the cards. (R5)
- [ ] Collect real chat and stage transcripts from rehearsals to use as test data.
- [ ] Check that chat references like "ask her again" resolve correctly against the transcript.
- [ ] Tune how much transcript goes in: too little loses the story, too much buries the latest moment.

## Show-readiness

- [ ] Do an end-to-end run in a real Zoom webinar with a few people typing.
- [ ] Time Stop to cards on screen. (C1)
- [ ] Test captions in the real room: mic placement, crowd noise, accuracy. (R5)
- [ ] Write a pre-show checklist: credentials set, captions running, stage app open on the stage device, display shared in Zoom.

## Later / maybe

- [ ] Filter out chat bots.
- [ ] Keep state across restarts.
