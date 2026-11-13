# sdp-test: Zoom webinar chat -> performer instructions

Prototype for the "Mission: Implausible" live-show pipeline. The audience is in
a Zoom webinar. Someone on stage presses **Start** on `/stage`, the audience
chats, then they press **Stop**. The round of chat goes to Claude, which judges
each message using `prompts/aggregate.md` and returns 3 lines for the performer.
The lines show on the `/stage` page and on the projector display.

The instructions live in `prompts/aggregate.md`. Edit that file to change
tone, rules, or output - no code changes needed.

No npm dependencies - built-in `http` and `fetch` only.

## Run it

```
cp .env.example .env   # fill in ANTHROPIC_API_KEY
export $(cat .env | xargs)
npm start
```

- `http://localhost:3000/stage` - Start/Stop button and the returned cards. Open on the performer's phone or tablet (use the laptop's LAN IP). Press Stop again to regenerate the same round.
- `http://localhost:3000` - projector / screen-share display, updates on every Stop.

### Getting chat in

The server collects chat from `POST /chat` with JSON `{"user": "...", "text": "..."}`,
only while a round is running. How Zoom webinar chat gets there is still open
(see `TODO.md`). To test without Zoom:

```
curl -XPOST localhost:3000/chat -d '{"user":"viewer1","text":"ask everyone what time they arrived"}'
```

### Stage captions

We make our own stage captions. Open `http://localhost:3000/captions` in Chrome on a machine
that hears the show audio (the OBS machine, or one with a mic in the room),
then click Start. Chrome's built-in speech recognition turns speech into
lines, which are posted to the server and logged as `[stage]`. The last
`TRANSCRIPT_LINES` (40) go into every batch, so the model knows what just
happened on stage. If the captions page isn't running, batches are chat only,
same as before.

## Test

```
npm test
```

Runs `test/aggregate.test.js`, a mocked-fetch check of the JSON parsing and
error paths in `src/aggregate.js` - no network or API key needed.

```
npm run try                       # sponsor's 50 sample chats -> 3 cards
node test/try.js my-chats.txt     # any file, one chat per line
node test/try.js test/fixtures/50-chats.txt test/fixtures/transcript.txt   # with stage captions
```

Calls the real API (needs `ANTHROPIC_API_KEY`). Use it to iterate on the prompt.

## Status

See `REQUIREMENTS.md` for what the system must do and `TODO.md` for what is left.
