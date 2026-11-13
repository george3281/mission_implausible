# TODO

Requirement numbers refer to `REQUIREMENTS.md`.

## Next

- [ ] Pick how Zoom webinar chat reaches `POST /chat`: browser script in HQ's Zoom web client, `webinar.chat_message_sent` webhook, RTMS, or a bot. Check whether Zoom's page CSP blocks a script posting to localhost. (F1)
- [ ] Confirm webinar settings: attendee chat on (not Q&A only), and who attendees can chat with.

- [ ] Run `npm run try` with and without `test/fixtures/transcript.txt` and compare the cards. This shows whether stage context fixes the nonsense output. (F4, F9)
- [ ] Test the captions page in the real room: mic placement, crowd noise, how accurate it is. (F9)
- [ ] Do an end-to-end run in a real Zoom webinar with a few people typing. (F1-F8)
- [ ] Time Stop to cards on the `/stage` page. (N1)

## Show-readiness

- [ ] Decide with the director how cards reach the actors: projector only, HQ reads them out, or an earpiece. (F12)
- [ ] Screen-share the HQ display (or add it in OBS) so webinar viewers see the cards. (F11)
- [x] Regenerate: pressing Stop again on `/stage` re-runs the same round.
- [ ] Write a pre-show checklist: env vars, captions page started, `/stage` open on the stage device, display shared in Zoom.

## Prompt

- [ ] Collect real chat from rehearsals and save it as fixtures in `test/fixtures/`.
- [ ] Check that chat references like "ask her again" resolve correctly against the transcript.
- [ ] Tune `TRANSCRIPT_LINES`: too few loses the story, too many buries the latest moment.

## Later / maybe

- [ ] Speaker labels or better accuracy: pull the webinar audio (Zoom RTMS gives transcripts) and run Whisper or Deepgram. Needs ffmpeg. Only do this if Chrome captions aren't good enough.
- [ ] Filter out third-party chat bots.
- [ ] Keep state across restarts. Right now a restart loses the chat buffer and transcript.
