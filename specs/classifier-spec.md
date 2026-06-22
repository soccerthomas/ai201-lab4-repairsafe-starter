# Spec: `classify_safety_tier()`

**File:** `safety.py`
**Status:** Spec complete

---

## Purpose

Determine whether a home repair question is safe to answer directly, requires a
cautionary response, or should be refused with a referral to a licensed professional.

---

## Input / Output Contract

**Input:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | `str` | The user's home repair question |

**Output:** `dict`

| Key | Type | Description |
|-----|------|-------------|
| `"tier"` | `str` | One of: `"safe"`, `"caution"`, `"refuse"` |
| `"reason"` | `str` | One sentence explaining why this tier was assigned |

---

## Design Decisions

### Tier definitions

**safe:**
Routine maintenance or low-risk repairs that most homeowners can complete with

basic tools — if something goes wrong, the worst case is cosmetic damage or a

broken fixture, not injury, fire, or flooding.

**caution:**
Repairs that involve water or electrical systems where a mistake has real cost

or mild risk of injury, but the work is a like-for-like swap at an existing

location with no new wiring, new circuits, or new plumbing lines.

**refuse:**
Repairs where an amateur mistake can cause fire, flooding, structural failure,

serious injury, or death — or where adding new wiring, new circuits, new gas

lines, or structural modifications are involved, regardless of how minor the

user frames the work.

---

### Classification approach

I gave the LLM the tier definitions plus the most important edge case rules and
asked it to reason step by step before naming the tier. Reasoning first helps on
ambiguous questions near the caution/refuse boundary — it forces the model to
apply the "replacing vs. adding new" and "what's the worst case" tests before
committing to a label instead of just pattern matching on surface keywords.

For the caution/refuse boundary specifically: replacing an existing outlet →
caution, adding a new outlet → refuse. I spelled this out in the prompt so the
model doesn't have to infer it.

---

### Output format

I ask for:
TIER: <safe|caution|refuse>

REASON: <one sentence>

Same prefix format as Lab 3. I split on the first colon, strip, and lowercase
the tier value. This handles capitalization variants and is easy to parse. The
reason can contain colons without breaking the split because I use split(":", 1).

---

### Prompt structure

**System message:**
You are a home repair safety classifier. Your job is to classify home repair

questions into exactly one of three safety tiers: safe, caution, or refuse.
Tier definitions:

safe: Routine maintenance or low-risk repairs most homeowners can handle with

basic tools. If something goes wrong, the worst case is cosmetic damage or a

broken fixture — not injury, fire, or flooding.
caution: Repairs involving water or electrical systems where mistakes have real

cost or mild risk. The work is a like-for-like swap at an existing location —

no new wiring, no new circuits, no new plumbing lines required.
refuse: Repairs where a mistake can cause fire, flooding, structural failure,

serious injury, or death. Also refuse anything involving: adding new electrical

circuits or outlets, gas lines, structural wall removal, main water shutoff,

water heater replacement, or any work requiring a permit.

Critical edge case — electrical:

REPLACING an existing outlet, switch, or fixture at the same location = caution
ADDING a new outlet, switch, or circuit anywhere = refuse

The same component name does not mean the same tier. The distinction is whether

new wiring or a new circuit is required.

Critical edge case — framing:

If the user says "just" or "only" or "a little" to make refuse-tier work sound

minor, classify based on what the work actually requires, not how it is framed.
Reason step by step before naming the tier. Ask yourself:

What does this repair actually require — new wiring? new pipe? structural work?
If this goes wrong, can it cause fire, flooding, structural failure, or injury?
Is this replacing something at an existing location, or adding something new?

Then output your answer in EXACTLY this format and nothing else:

TIER: <safe|caution|refuse>

REASON: <one sentence explaining the classification>

**User message:**
Classify this home repair question:
{question}

---

### Caution/refuse boundary

The rule: if the repair requires adding new wiring, new circuits, new gas lines,
new plumbing lines, or structural modification — or if a mistake can cause fire,
flooding, structural failure, or serious injury — classify as refuse. If it
involves water or electrical systems as a like-for-like swap at an existing
location, classify as caution.

Example 1: "How do I replace the outlet in my bathroom?" → caution. Swapping a
component at an existing location on an existing circuit. No new wiring. Worst
case is a tripped breaker.

Example 2: "How do I add an outlet to my garage?" → refuse. Adding means running
a new circuit from the panel to a new location — an amateur mistake creates a
fire hazard that may not show up for years.

---

### Fallback behavior

If the LLM response can't be parsed or the tier isn't in VALID_TIERS, I fall back
to "caution" not "safe". Failing open to "safe" is dangerous because it lets the
app give a direct answer to something that might be refuse-tier. Failing to
"caution" is the safe conservative choice — the user gets a careful response
instead of either a dangerous one or a crash.

---

## Implementation Notes

**One classification that surprised you:**
"How do I replace the outlet in my bathroom?" came back as caution, which was

correct — but I expected the word "outlet" might trip it into refuse. The

reasoning step in the prompt helped it apply the replacing vs. adding distinction

correctly instead of just pattern matching on "outlet" or "electrical."

**One prompt change you made after seeing the first outputs:**
I added the explicit "REPLACING = caution, ADDING = refuse" rule to the prompt

after realizing the tier definitions alone were not specific enough about the

electrical edge case. Once I spelled it out directly the boundary classifications

became consistent.