import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# --------------------------------------------------
# SETUP
# --------------------------------------------------

# Load API key from .env
load_dotenv()
client = OpenAI()

# Project directories
BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"


# --------------------------------------------------
# SCOUT'S RESEARCH INSTRUCTIONS
# --------------------------------------------------

SCOUT_INSTRUCTIONS = """
You are Scout, a researcher working for a comic book publisher.

Your primary purpose is to identify and evaluate
cultural phenomena, niche audiences, emerging
interests, communities, and ideas with meaningful
cultural traction.

You are NOT a conventional trend reporter.

Your research should help an entertainment
development team understand:

- What people are interested in
- Which communities are actively engaged
- What is gaining or losing cultural momentum
- Who is influencing or participating in a phenomenon
- What makes an idea culturally significant
- Whether commercial interest is visible
- Which topics deserve further investigation for narrative potential

Cultural momentum is the primary objective.

RESEARCH REQUESTS

Users may submit questions, statements, topics,
hypotheses, or instructions.

Do not require requests to be phrased as questions.

Interpret the user's intention and select the
appropriate research approach.

There are three primary approaches:

1. BROAD DISCOVERY

Use when the request is open-ended or the user
does not have a specific subject in mind.

Explore at least eight substantially different
cultural territories when feasible.

Possible territories include:
- Music and underground art or performance
- Sports and recreation
- Gaming and fandom
- Fashion and beauty
- Technology and digital culture
- Crafts and maker communities
- Food and local cultural scenes
- Spirituality and folklore
- Relationships and social behaviors
- Science and unusual hobbies

Identify up to five distinctive findings.

Favor unexpected discoveries with evidence of
meaningful participation, sustained engagement,
or changing cultural momentum.

Do not return multiple versions of the same
underlying phenomenon.

2. FOCUSED INVESTIGATION

Use when the request identifies a particular
topic, community, interest, or cultural phenomenon.

Investigate that subject in depth.

Return one primary finding, with additional
findings only when they represent genuinely
distinct and relevant developments.

Do not introduce unrelated communities simply
to reach a target number of findings.

3. EXPLORATORY CONNECTIONS

Use when the request investigates possible
relationships between interests, communities,
industries, or cultural phenomena.

Investigate whether the connections are
documented and culturally meaningful.

Identify relevant audiences, behaviors,
influential people, collaborations, and
evidence of engagement.

Distinguish established connections from
plausible but unverified hypotheses.

Return only findings supported by evidence.

These approaches are flexible and may overlap.
Choose the approach that best serves the request.

RESEARCH PRIORITIES

1. AUDIENCE

Identify who participates in or follows
the phenomenon.

Look for recognizable communities, shared
interests, identities, behaviors, and rituals.

Do not invent audience demographics or size.

2. ENGAGEMENT

Seek evidence of sustained participation:

- Recurring discussions
- Dedicated online communities
- Fan-generated content
- Creators and organizers
- Events and gatherings
- Active participation and debate
- Repeat engagement

A small, intensely engaged audience may be
more significant than a large passive audience.

3. CULTURAL MOMENTUM

Investigate whether interest is:

- Growing
- Stable
- Declining
- Changing in character
- Spreading into adjacent communities

Prioritize evidence from the past 12 months,
but examine older material for historical context.

Where possible, compare activity across
different periods.

Do not mistake a single viral event or
article for sustained growth.

If there is insufficient evidence of growth,
state that momentum is unverified.

4. KEY FIGURES

Identify notable people who are meaningfully
connected to the research subject.

These may include:

- Community leaders
- Creators and organizers
- Athletes
- Musicians and performers
- Public figures with documented interests
- People connecting different audiences
- Individuals involved in relevant collaborations

For each person, explain their connection
and why it matters.

Include supporting sources.

Do not invent personal interests, affiliations,
endorsements, or relationships.

Do not assume someone is influential within
a community merely because they are famous.

If no relevant figures can be verified,
return an empty list.

5. CULTURAL SIGNIFICANCE

Investigate what makes the phenomenon distinctive:

- Shared values or worldviews
- Language and aesthetics
- Rituals and behaviors
- Cultural tensions
- Historical context
- Relationships to adjacent interests
- Reasons for sustained enthusiasm

6. COMMERCIAL SIGNALS

Look for evidence of commercial interest:

- Products and merchandise
- Events and ticket sales
- Collaborations
- Licensing
- Creator businesses
- Memberships and subscriptions
- Consumer spending when documented

Distinguish actual commercial activity from
speculative commercial potential.

Do not assume cultural popularity translates
directly into willingness to pay.

7. EVIDENCE QUALITY

Favor direct community participation and
primary sources over generalized trend articles.

Seek at least two independent sources per
major finding when available.

Use web search to verify important claims.

Never invent statistics, source URLs,
quotes, demographics, or growth rates.

Distinguish:
- Verified observations
- Reasonable interpretations
- Unverified hypotheses

A lack of evidence should be explicitly reported,
not concealed.

RESEARCH STANDARDS

Prioritize depth, originality, and credibility.

Prioritize:
- Emerging subcultures over mainstream trends (unless the trend is
  supported by credible evidence of exceptional growth)
- Communities with passionate and distinct language or sense of identity
- Intense discussion and emotional investment in positive changes
  for the future


Avoid:
- Generic mainstream trends without a specific angle
- Celebrity gossip
- Broad demographic categories presented as subcultures
- Invented community names or invention of any kind
- Unsupported growth claims
- Seasonal spikes presented as lasting momentum
- Overstating the significance of isolated examples

Use web search to find real evidence.

Do not prioritize short-lived viral moments
without evidence of deeper cultural engagement.

Investigate competing explanations when relevant.

If a request is broad, search widely before
selecting the strongest findings.

If a request is focused, investigate the subject
thoroughly rather than broadening unnecessarily.

The final report should help the user decide
what deserves further attention and why.

"""

# --------------------------------------------------
# RESEARCH FUNCTION
# --------------------------------------------------

def run_scout(research_request):
    """
    Research a cultural topic and return a
    structured Cultural Intelligence Report.
    """

    if not isinstance(research_request, str):
        raise ValueError("Research request must be text.")

    research_request = research_request.strip()

    if not research_request:
        raise ValueError("Please enter a research request.")

    print("\nStarting AWA Scout...")
    print(f"Researching: {research_request}")

    prompt = f"""
    Conduct cultural intelligence research in response
    to the user's request.

    USER RESEARCH REQUEST:
    {research_request}

    Determine whether this requires broad discovery,
    focused investigation, exploratory connections,
    or a combination of these approaches.

    Your report should prioritize:

    1. Audience existence and characteristics
    2. Evidence of meaningful engagement
    3. Cultural momentum over time
    4. Relevant notable people and key figures
    5. Cultural significance and context
    6. Commercial signals, where available
    7. Evidence quality and research limitations

    Adapt the number of findings to the request.

    Broad discovery may return up to five findings.

    Focused investigation may return just one
    detailed finding.

    Do not manufacture findings to fill the report.

    Return ONLY valid JSON following this structure:

    {{
        "research_request": "...",
        "research_approach": "discovery / focused / connections",
        "summary": "Executive research summary",
        "findings": [
            {{
                "name": "Name of finding",
                "description": "What this phenomenon is",
                "category": "Relevant cultural territory",
                "history": "Background and development",
                "audience": "Who participates or follows it",
                "engagement": "Evidence of participation",
                "momentum": {{
                    "status": "growing / stable / declining / changing / unverified",
                    "assessment": "Explanation of momentum",
                    "historical_comparison": "Earlier versus recent activity"
                }},
                "key_figures": [
                    {{
                        "name": "Person's name",
                        "field": "Area of activity",
                        "connection": "Documented relationship to the topic",
                        "significance": "Why this person matters",
                        "source_urls": []
                    }}
                ],
                "cultural_significance": "Why the phenomenon matters",
                "commercial_signals": "Documented commercial activity",
                "commercial_potential": "Evidence-based interpretation",
                "related_communities": [],
                "narrative_themes": [],
                "evidence_strength": "weak / moderate / strong",
                "unverified_claims": [],
                "sources": [
                    {{
                        "platform": "Source platform",
                        "url": "https://...",
                        "relevance": "What this source demonstrates"
                    }}
                ]
            }}
        ],
        "overall_assessment": "What the research suggests",
        "research_limitations": []
    }}

    Requirements:

    - Use the exact field names shown.
    - Return actual values, not the placeholder examples.
    - Use an empty list when no verified key figures exist.
    - Do not invent evidence to complete a field.
    - Explain uncertainty explicitly.
    - Separate documented commercial signals
      from speculative commercial potential.
    - Include source URLs supporting important claims.
    - Do not use a numerical opportunity score.
    """

    # ----------------------------------------------
    # OPENAI RESEARCH
    # ----------------------------------------------
    
    response = client.responses.create(
    model="gpt-5.1",
    tools=[
        {
            "type": "web_search",
            "search_context_size": "high"
        }
    ],
    tool_choice="required",
    instructions=SCOUT_INSTRUCTIONS,
    input=prompt,
    max_output_tokens=12000
)

    # ----------------------------------------------
    # PARSE JSON
    # ----------------------------------------------

    raw_text = response.output_text or ""


    # Check whether the research response completed.
    if response.status == "incomplete":
        raise ValueError(
            f"Scout's research was incomplete: "
            f"{response.incomplete_details}"
        )

    if not raw_text.strip():
        raise ValueError(
            "Scout returned an empty research response."
        )

    # First, try parsing the original response.
    try:
        data = json.loads(raw_text)

    except json.JSONDecodeError:

        print("Formatting Scout's response as JSON...")

        # Use a second call WITHOUT web search.
        formatting_response = client.responses.create(
            model="gpt-5.1",
            instructions="""
            Convert the supplied research response into
            a valid JSON object.

            Preserve all research findings, source URLs,
            qualifications, and uncertainty.

            Do not add new facts or conduct research.

            The result must contain a top-level
            "findings" array.

            Return only valid JSON.
            """,
            input=raw_text,
            text={
                "format": {
                    "type": "json_object"
                }
            },
            max_output_tokens=12000
        )

        if formatting_response.status == "incomplete":
            raise ValueError(
                "Scout's JSON formatting response "
                "was incomplete."
            )

        data = json.loads(
            formatting_response.output_text
        )


    if not isinstance(data, dict):
        raise ValueError(
            "Scout returned an unexpected report format."
        )

    if not isinstance(data.get("findings"), list):
        raise ValueError(
            "Scout's report must contain a findings list."
        )

    # Preserve the original request reliably.
    data["research_request"] = research_request

    # Record when the research was conducted.
    data["research_date"] = datetime.now(
        timezone.utc
    ).isoformat()

    # ----------------------------------------------
    # SAVE REPORT
    # ----------------------------------------------

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d_%H-%M-%S-%f"
    )

    filename = (
        RESULTS_DIR / f"scout_{timestamp}.json"
    )

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(f"\nSaved report to {filename}")

    # ----------------------------------------------
    # DISPLAY TERMINAL SUMMARY
    # ----------------------------------------------

    print(
        "\nResearch approach:",
        data.get("research_approach", "Unknown")
    )

    print("\nSummary:")
    print(data.get("summary", ""))

    findings = data["findings"]

    print(f"\nFound {len(findings)} findings.")

    for index, finding in enumerate(
        findings, start=1
    ):
        print(
            f"\n{index}. "
            f"{finding.get('name', 'Unnamed finding')}"
        )

        print(finding.get("description", ""))

        momentum = finding.get("momentum", {})

        if isinstance(momentum, dict):
            momentum_status = momentum.get(
                "status", "unverified"
            )
        else:
            momentum_status = str(momentum)

        print(f"Momentum: {momentum_status}")

        print(
            "Evidence:",
            finding.get(
                "evidence_strength",
                "Not assessed"
            )
        )

    # Return results to the calling application.
    return data


# --------------------------------------------------
# RUN DIRECTLY FROM TERMINAL
# --------------------------------------------------

if __name__ == "__main__":

    if len(sys.argv) > 1:
        request = " ".join(sys.argv[1:])
    else:
        request = (
            "Discover overlooked cultural phenomena "
            "and highly engaged niche audiences "
            "with meaningful cultural momentum."
        )

    run_scout(request)