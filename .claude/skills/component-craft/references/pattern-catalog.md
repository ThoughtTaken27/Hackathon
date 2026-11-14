# Pattern catalog

Each pattern lists its anatomy, the details that make it feel finished, when not to use it, and its accessibility contract. Sources are affectui.com/components/<slug> and aisdkagents.com/ai-components/<slug>, observed Oct 17, 2026. Fit every pattern to the product's real data. These are anatomies, not skins.

## Agent work

**Thinking state / thinking loader**
- Anatomy: a header ("Thinking 4s", which becomes "Worked for 18s") with a chevron that rotates -90° to 0° over 260ms. Below it, a timeline of 20px icon nodes on a 1px rail, and source chips that pop in staggered at 120ms + 160ms each.
- Details: the loader is an eight-ray spinner (800ms linear, opacity 1 to .18), and the label rolls between phases while the box glides to the new label's width. The spinner and check share one square. Nodes are never removed while live. The newest node is the active one, and the active state only moves forward.
- Not for waits under 0.5-1s (it would only flash) or measurable progress (use a bar).
- A11y: `role=status` with a polite live region. Decorative copies are aria-hidden.

**Tool call card / group**
- Anatomy: one line holding the tool icon, the name in mono, a summary, the status and a timer. It opens to the arguments and the result (grid 0fr to 1fr). A group renders as one quiet line, "Using tools…" (shimmering), which becomes "Ran 4 tools" with the icons stacked.
- Details: code wraps instead of scrolling sideways, and capped blocks fade out at the bottom. An error shows the message plus Retry inside the card. Everything truncates before it overflows.
- Not for end users who never care about JSON. Show a one-line status and keep the details in a log.

**Agent plan / steering**
- Anatomy: a card holding a quiet status line, then the goal, then the steps. The marker goes from a ring with the number, to a spinner, to a check that draws itself. The right column holds remove, a live timer, and the duration. A tray below carries status ("5 steps · ~10 sec").
- Details: the drag grip shows on hover but is always visible on touch. "Add step" folds away once the plan is running. A failed step shows an error line plus a way back in. In steering, a queued note glides into the step that picks it up.

**Task tray (background agents)**
- Anatomy: a pill that says one thing ("1 needs you", "2 running", or "Done"); pressing it shows each task's progress.
- Details: rows read title over present-tense status ("Reading 214 orders"). Needs-you rows have a dot and running rows have a spinner arc. Each row has a Stop control.

**Agent inbox / lanes**
- Inbox: filter tabs with rolling counts, and a semibold width reserved so tabs never nudge. Status tags are all as wide as the longest. Rows unfold to their last steps with one next action and glide to their new place. Status changes are announced once.
- Lanes: blocks grow out of "now", so they never poke past it. The state tag collapses while the agent works. A needs-you flag sits where the block meets now.

**Run recovery**
- Anatomy: "Weekly digest · Stopped at step 4 of 6", then "3 steps done · 11.5s" (foldable), then the failing step with "Failed after 41s" and its cause, then whether it can resume, then "Run again" or "Resume".

## Approvals and decisions

**Approval card**
- Anatomy: a white card (the action as the title, its effect as the subtitle, a risk tag, a preview panel of key-value rows) on a gray tray. The tray holds the countdown on the left and Deny and Approve on the right, with kbd hints on desktop only.
- Details: the countdown pauses when the card is hovered or focused or once answering starts. When answered, the request lays over the resolved row and morphs into it ("Approved: Send campaign email"). Button labels blur-crossfade (out 220-280ms ease-in with blur 3px, in 350-500ms with blur 4px→0). On narrow cards the buttons share the full width and the hints go. Deny is the safe default. "Always allow" is optional and closes the card.
- Not for reversible actions (just do them and offer undo) or bulk triage (use a decision inbox).
- A11y: `role=group` named by the title. The decision is announced. While processing, the card is aria-busy and the buttons aria-disabled, so focus is never lost.

**Decision inbox**: one-click answers. Answered rows confirm, then fold away with a height transition, and the count heading is a live region. Leave room around the buttons so the fold's clipping never cuts their ring.

**Questions panel**: "1 of 3" on top, numbered options (1/2/3 keys), "Pick any that apply." for multi-select, Back / Skip all / Next ↵.

**Guardrail notice**: the type tag ("Prompt injection"), one concrete sentence, and two choices (inspect, plus proceed or request review).

## Chat surface

**Message actions**: four actions under assistant messages only (copy, retry, rate, read aloud). Copy morphs into a check: two stacked icons, one blurring out at scale .6 while the other comes in, opacity 200ms and transform 300ms, then the tick draws over 340ms after a 60ms delay. Regenerate spins once per press. Thumbs pop and ask why. Hide the bar while streaming and show Stop instead.

**Interrupted reply**: keep the partial text, then a quiet line ("You stopped this reply" / "Connection lost" / "Reached the length limit") with Continue.

**Model unavailable / limit reached**: a title naming the model, a one-sentence cause, "Your message is saved.", an auto-retry countdown or reset time, and one alternative action.

**AI answer / cited answer**: status phases ("Reading 6 sources", then "Writing", then "Answer") with a shimmer on the working label. Source cards scroll sideways. Citation chips preview their source and keep a larger invisible hit area on touch. Follow-ups come last. The answer is aria-busy while it streams. (Useful for "show why to trust it": every output shows its source, AGENTS.md §2.)

**Composer / prompt input**: one text line that grows by one line while typing. Clicking anywhere on the card focuses the field. Model, voice and send controls on the right. Hover effects apply only while actionable.

**Slash / mention / command menu**: a gray tray around a white card. Rows are single-line (icon, name, muted hint), and the name wins over the hint when space runs out. The row that just ran flashes briefly. Phones get no shortcut keys or hints. The menu should never be the only way to reach something.

**Attachments / dropzone**: rows grow in at 420ms. Removal flashes the row (280ms) and then folds it after 200ms, and a leaving row stops reacting immediately. The progress bar folds away 250ms after done. The done check pops. An error shakes once and gives a plain reason. The foot tray reads "Uploading 2 of 2 · 0.2 of 6.8 MB". Touch gets 40px buttons and tap phrasing.

**Voice session**: one card holding the wave state ("Listening", "Thinking", "Speaking") and a mono timer. The transcript is user muted and assistant in ink, and tool calls show inline as 12px muted lines where they happened. At the bottom: Mute on the left, End on the right.

**Session list**: New chat on top, pinned rows first, row badges limited to "Running" and "Unread". Options sit behind one button per row.

**Starter prompts**: 3-4 prompts picked from the person's real context, each with its source ("Yesterday", "Linear"), plus "More ideas". (For a demo: these are your three golden-path inputs, AGENTS.md §4.)

## Notices

**Toaster**: a stack where the cards behind show only their edge, fanning out on hover. A promise toast morphs spinner → check, and the arc closes into a ring where it is. A hairline timer stops whenever the timer stops (hover, focus, hidden tab). Swipe is never the only exit. On phones it is full width with 12px gutters. Errors go in an alert region so they are read first. Use toasts for confirmations and background results, never for form errors or decisions.

**Run finished toast**: what it was, how it went with its duration and result, and one Open button. Runs that finish together share one toast that counts up instead of stacking.

**Notify when done**: "Reading 14 of 40 sources · About 9 min left", then a "Notify me" toggle.

**Notification stack**: a few persistent notices. Only the front card is focusable, and three or four at most before you need an inbox.

## Controls

**Segmented control**: 2-6 options of equal width, each as wide as the widest. The pill's leading edge leads and the trailing edge follows, so it stretches and settles. Regular and semibold label copies crossfade, so the width never changes. On touch, a tap picks on lift so a scroll never picks, and every option is at least 40px.

**Button**: sm 32, md 40, lg 48. The primary is dark with a light edge and a 1px ring. Press scale .97. Loading sweeps a light band across a copy of the label. Width morphs clip while gliding, and the changed parts blur in.

**OTP input**: one real input under the boxes. One ring glides from box to box. On error only the borders turn red, and they shake once. On success the boxes slide together into a "Verified" pill.

**Numbers**: digits roll individually (new column from -35%, edge mask 14%/86%). Only the changed digit moves, and the label carries the number for screen readers.

**Context window / usage meter**: a field of cells or a stacked bar where the parts keep their place and colour and only the widths glide. Gaps come out of the bar, not added to it. Amber appears only as one small dot.

## Rejected as decoration (from the same corpora)

Gradient floors and glow clouds, tilt cards, pink and violet gradient glows, and infinite breathing on idle elements. Use these only when a brief explicitly asks for a marketing surface.
