from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, VALID_TIERS

_client = Groq(api_key=GROQ_API_KEY)

_SYSTEM_PROMPT = """You are a home repair safety classifier. Your job is to classify \
home repair questions into exactly one of three safety tiers: safe, caution, or refuse.

Tier definitions:
- safe: Routine maintenance or low-risk repairs most homeowners can handle with basic \
tools. If something goes wrong, the worst case is cosmetic damage or a broken fixture \
— not injury, fire, or flooding.
- caution: Repairs involving water or electrical systems where mistakes have real cost \
or mild risk. The work is a like-for-like swap at an existing location — no new wiring, \
no new circuits, no new plumbing lines required.
- refuse: Repairs where a mistake can cause fire, flooding, structural failure, serious \
injury, or death. Also refuse anything involving: adding new electrical circuits or \
outlets, gas lines, structural wall removal, main water shutoff, water heater \
replacement, or any work requiring a permit.

Critical edge case — electrical:
- REPLACING an existing outlet, switch, or fixture at the same location = caution
- ADDING a new outlet, switch, or circuit anywhere = refuse
The same component name does not mean the same tier. The distinction is whether new \
wiring or a new circuit is required.

Critical edge case — framing:
If the user says "just" or "only" or "a little" to make refuse-tier work sound minor, \
classify based on what the work actually requires, not how it is framed.

Reason step by step before naming the tier. Ask yourself:
1. What does this repair actually require — new wiring? new pipe? structural work?
2. If this goes wrong, can it cause fire, flooding, structural failure, or injury?
3. Is this replacing something at an existing location, or adding something new?

Then output your answer in EXACTLY this format and nothing else:
TIER: <safe|caution|refuse>
REASON: <one sentence explaining the classification>"""


def classify_safety_tier(question: str) -> dict:
    """
    Classify a home repair question into one of three safety tiers.

    Returns a dict with:
      - "tier"   : str — one of "safe", "caution", "refuse"
      - "reason" : str — a brief explanation of why this tier was assigned
    """
    # 1. build the user message
    user_message: str = f"Classify this home repair question:\n\n{question}"

    # 2. call the LLM
    try:
        response = _client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0,
        )
        text: str = response.choices[0].message.content
    except Exception as e:
        return {
            "tier": "caution",
            "reason": f"Classification unavailable due to API error: {e}",
        }

    # 3. parse TIER: and REASON: prefixes
    tier: str = ""
    reason: str = ""
    for line in text.splitlines():
        line = line.strip()
        if line.upper().startswith("TIER:"):
            tier = line.split(":", 1)[1].strip().lower()
        elif line.upper().startswith("REASON:"):
            reason = line.split(":", 1)[1].strip()

    # 4. validate — fail closed to caution if unparseable
    if tier not in VALID_TIERS:
        found: str = next((t for t in VALID_TIERS if t in text.lower()), "")
        if found:
            tier = found
        else:
            tier = "caution"
            if not reason:
                reason = f"Could not parse tier from response: {text[:120]}"

    return {"tier": tier, "reason": reason}