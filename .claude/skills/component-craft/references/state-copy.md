# State copy

The copy is part of the component. The examples below are verbatim from live demos on aisdkagents.com and affectui.com (Oct 17, 2026). Swap in the product's real nouns; don't copy the example domains.

## The shape

A failure, limit or block:
- **Title**: what happened, with the subject named. "Claude Sonnet 4.5 is busy", "Message limit reached", "Out of credits", "Too many requests".
- **Cause**: one plain sentence that says why. "It has more requests than it can take right now." / "Tried 3 times without an answer."
- **Fact instead of reassurance**: "Your message is saved." (never "Don't worry!").
- **What happens next, with a number**: "It will try again on its own." plus a countdown ("7s"), or "Resets in 3h 13m".
- **One action named by its effect**: "Try now", "Use the cached result", "Add credits", "Continue", "Run again". Avoid "OK", "Submit" and "Got it".

A stopped reply keeps its partial text and adds one quiet line plus Continue: "You stopped this reply" / "Connection lost" / "Reached the length limit".

## Unknown input (health and safety apps)

- Never say "safe", "no risk" or "all clear" for something the system doesn't know (AGENTS.md §0.7).
- Name it and say what we know: "Not in our list: ‘Zyloprim 100’. We couldn't check it." Then the next step: "Ask your pharmacist about this one."
- Every result screen carries "Prototype, not medical advice."

## Live status (present tense, 2-4 words, real numbers)

- "Reading 214 orders", "Comparing amounts", "Reading 14 of 40 sources", "Planning the research…"
- "Running tools · 1 of 2 done · 1.6s", "Stopped at step 4 of 6", "Step 2 of 5"
- Time left is approximate and rounded: "About 9 min left", "4s left".
- The pending verb carries the request: "Wants to email the customer".
- Lead with what needs the person: "1 needs you" sits above "2 running".

## Finished (the record that stays)

- "Finished in 4m 12s · Found 3 duplicate refunds". Duration first, then the result in the product's words.
- "Ran 4 tools · query_analytics, search_logs, list_deploys, post_to_slack · 6.0s"
- "Worked for 18s", "3 steps done · 11.5s"
- An approval folds to a single row: "Post to Slack, approved." with "Show what was asked".
- "Failed after 41s" plus the cause, then what is possible ("This step cannot be picked up halfway.") and "Run again".

## Approvals

- The title is the action ("Send campaign email", "Roll back production"). The subtitle is its effect ("Production goes back to the build from Oct 5.").
- A destructive action names its verb on the button ("Roll back") instead of "Approve".
- Risk is a small tag beside the title, as glyph plus word ("Medium risk"). Safe actions carry no tag.
- A countdown pauses once the person starts answering ("Paused").
- Arguments as key-value rows ("Subject: What's new in October"). Long lists end in "+38 more".

## Lists, schedules, inboxes

- A summary line that leads with the exception: "One failed on its last run."
- Row meta: "Every hour · in 12m", "Running now", "Failed 3h ago: The API key has expired." followed by Retry.
- Relative time is short: "47m ago", "2h", "Yesterday".
- Paging: "1 of 3", "1/4", "5 / 5".

## Guardrails and safety

- Name the event concretely: "A page the agent read told it to send your order history to an outside address."
- Say what was done for the person: "Card and contact details were replaced before your message reached the model."
- Pair two choices: "What was caught" (inspect) and "Run anyway" / "Request review".

## Empty and hint

- Hints teach by doing: "Hover the stack to spread it out. Swipe to dismiss."
- Touch copy differs from mouse copy: "Drop files here or browse" becomes tap phrasing on touch, and keyboard hints are removed.
- State limits up front: "PDF, PNG, JPG · up to 25 MB each". Rejections give the reason: "Larger than the 25 MB limit".

## Bans

No exclamation marks, "Oops", "Something went wrong" without a cause, "Please try again later" without a time, emoji, or marketing adjectives. Keep "successfully" out of success messages ("Saved", not "Successfully saved!"). Don't chain more than two meta items with middle dots.
