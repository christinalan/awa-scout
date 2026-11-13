import os
import streamlit as st
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
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    api_key = st.secrets.get("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

# Project directories
BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"

# Covers both the report text and the model's reasoning tokens.
MAX_OUTPUT_TOKENS = 32000


def check_response_complete(response, stage):
    """Reject truncated responses before parsing or saving; never retry implicitly."""
    if response.status != "incomplete":
        return
    details = response.incomplete_details
    reason = details.get("reason") if isinstance(details, dict) else getattr(details, "reason", None)
    if reason == "max_output_tokens":
        raise ValueError(
            f"Scout reached its {MAX_OUTPUT_TOKENS:,}-token output limit during {stage} "
            "before the report was complete. No report was saved and no automatic "
            "retry was made. Try a more focused request or fewer findings."
        )
    raise ValueError(f"Scout could not complete {stage} (reason: {reason or 'unknown'}). No report was saved.")


# --------------------------------------------------
# SCOUT'S RESEARCH INSTRUCTIONS
# --------------------------------------------------

SCOUT_INSTRUCTIONS = """
You are Scout, a researcher working for a comic book publisher.

Your primary purpose is to identify and evaluate
cultural phenomena, niche audiences, emerging
interests, communities, and ideas with meaningful
cultural traction.

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

For testing, compare a small selection of relevant
cultural territories, then investigate only the
single strongest candidate in depth.

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

Return at most one distinctive finding per research run
while testing. Return no findings if none are supported.

Favor unexpected discoveries with evidence of
meaningful participation, sustained engagement,
or changing cultural momentum.

Do not return multiple versions of the same
underlying phenomenon.

2. FOCUSED INVESTIGATION

Use when the request identifies a particular
topic, community, interest, or cultural phenomenon.

Investigate that subject in depth.

Return one primary finding only while testing.
Include relevant developments within that finding.

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

For each suggested audience, investigate where it actually
gathers: named subreddits, publicly documented Discord
servers, specialist forums, clubs, or other communities.
Support the connection with a direct discussion, community
page, or official directory explaining its relevance to
the phenomenon. A broad interest overlap alone is not
evidence that a community participates in this phenomenon.
Distinguish a directly observed discussion from a community
whose stated focus is relevant but participation is unverified.
Do not claim access to private Discord conversations.
Never invent server names, invite links, membership totals,
activity levels, or audience demographics. Prefer public
community home pages or official join pages to guessed invites.
Include counts only when explicitly available in a source,
with the measurement date and direct URL. Membership is not
the same as active participation or total audience size.
If no gathering place can be verified, return an empty list.

Make audience descriptions concrete rather than generic personas.
For each distinct, supported group, explain its specific relationship
to this topic: what it makes, seeks, shares, or responds to and why.
Prioritize multiple varied, named examples with direct sources:
actual creators, works, projects, posts, collections, or discussions.
For an aesthetic, explain the observable qualities in those examples
rather than merely labeling people as artists or photographers.
Collect as many useful, nonredundant examples as evidence supports;
never pad a group with imagined examples or inferred affiliations.
When a public community is identified, actively look for its published
membership and activity counts. Record exactly what is counted,
the observation date or source period, and the direct supporting URL.
If counts cannot be verified, omit them instead of estimating.

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

Find and list concrete, named examples rather than only
describing commercial activity in general terms. Look for
specific products, paid events, campaigns, crowdfunding
projects, subscriptions, licensing deals, and businesses
directly connected to the finding. Prefer official product
pages, campaign pages, ticket listings, or announcements.

In commercial_signals, give a short synthesis followed by
a Markdown bullet list. Each example must include the
actual product/project/event name as a clickable source
link, who offers it, what is being sold or monetized, and
what the evidence demonstrates. Include dates, prices,
sales, backers, or funding only when explicitly documented
in the cited source, with currency and measurement period
where relevant. A listed price or active campaign shows
an offer, not proven sales or demand; label that distinction.
Prioritize several distinct, well-supported examples when
available, without padding the list to meet a quota.
If no examples can be verified, say so explicitly instead
of suggesting hypothetical products or inventing numbers.

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

SOURCE DISCOVERY STRATEGY

Research cultural phenomena where participation
actually occurs, not only where journalists
and trend analysts report on them.

Actively consider the following sources:

COMMUNITY PLATFORMS
- Reddit: discussions, niche subreddits,
  recurring participation, community evolution
- Discord and independent forums:
  organized communities and sustained engagement
- Other relevant online communities

CREATOR AND SOCIAL PLATFORMS
- YouTube: creators, audience participation,
  recurring themes, and fandom ecosystems
- TikTok: emerging cultural language, creators,
  aesthetics, and visible engagement
- Instagram: visual communities, creators,
  and relevant collaborations
- Twitch and other live platforms when relevant
— Podcasts and Kickstarter campaigns with sizeable audiences

CULTURAL AND INDUSTRY SOURCES
- Independent cultural publications
- Interviews and creator profiles
- Event organizers and community websites
- Industry reporting
- Academic and historical research
- Search-interest data where available

SOURCE PRIORITIZATION

1. Prioritize firsthand evidence of participation.
2. Seek independent corroboration for major claims.
3. Use secondary reporting for context and history.
4. Use commercial data to evaluate market activity.
5. Include sources that challenge the initial hypothesis.

When appropriate, search specific platforms
using targeted queries.

If relevant platform content is inaccessible
or cannot be verified, state that limitation.

For each significant finding, explain which
sources support the assessment of cultural
momentum and which questions remain unanswered.

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

Write the research summary as 1-2 concise sentences
synthesizing what the evidence shows in response to
the user's inquiry. Do not list or repeat finding
titles or write a table of contents in prose.
For focused inquiries, lead with the main answer
and the most meaningful supporting insight.
For broad discovery, summarize the strongest patterns
or contrasts across findings without forcing a shared
theme where none is supported. Preserve material
uncertainty and avoid unsupported generalizations.

ACRONYMS AND READER ACCESSIBILITY

Write for an interested reader who may be unfamiliar
with the community's terminology. Spell out obscure,
specialist, or potentially ambiguous acronyms on first
use in each research section, followed by the acronym
in parentheses if it will be used again. Sections are
read independently; do not assume the reader has read
History before Audience or another section.

For example: tabletop role-playing games (TTRPGs).
Do not explain universally familiar abbreviations
unless their meaning is ambiguous in this context.
Prefer plain language over introducing an acronym
that is used only once.

When unfamiliar acronyms recur frequently and a key
would help, include a compact "Acronym key: TERM =
full meaning; ..." in the finding's existing history
text. Include only terms actually used in that finding.
This supplements first-use explanations in other
sections; it does not replace them. Verify meanings
from context and sources; never guess an expansion.
Do not add JSON fields or put acronym definitions
into the audience list as if they were audience groups.

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

    TESTING LIMIT: Return at most ONE finding for every research
    approach, including discovery, focused, and connections.
    Research only the strongest relevant candidate in depth.
    Keep all requested sections, examples and source evidence
    for that finding. Do not create extra findings or research
    multiple candidates in depth. Return [] if none is supported.

    Do not manufacture findings to fill the report.

    Keep explanations concise and avoid repeating the same background
    across sections. Preserve concrete examples, citations and uncertainty.

    Return ONLY valid JSON following this structure:

    {{
        "research_request": "...",
        "research_approach": "discovery / focused / connections",
        "summary": "1-2 sentence synthesis answering the inquiry, without listing finding titles",
        "findings": [
            {{
                "name": "Name of finding",
                "description": "What this phenomenon is",
                "category": "Relevant cultural territory",
                "history": "Background and development",
                "audience": "Who participates or follows it",
                "audience_groups": [
                    {{
                        "name": "Short, supported audience group name",
                        "description": "Topic-specific explanation of this group's interests, practices, or aesthetic, grounded in the examples",
                        "source_urls": [],
                        "examples": [
                            {{
                                "name": "Actual creator, work, project, post, or discussion",
                                "description": "Specific observable details showing the group's connection to the topic",
                                "url": "https://..."
                            }}
                        ]
                    }}
                ],
                "audience_communities": [
                    {{
                        "audience_group": "Audience group named in the audience text",
                        "name": "Verified community name",
                        "platform": "Reddit / Discord / forum / other platform",
                        "url": "https://...",
                        "description": "What demonstrates this audience gathers here and its connection to the phenomenon; distinguish observed participation from stated relevance",
                        "evidence_url": "https://...",
                        "metrics": []
                    }}
                ],
                "engagement": "Evidence of participation",
                "engagement_evidence": [
                    {{
                        "name": "Name of event, project, creator, publication, or community",
                        "evidence_type": "event / project / publication / community",
                        "description": "Documented activity and why it demonstrates engagement",
                        "source_url": "https://...",
                        "metrics": []
                    }}
                ],
                "momentum": {{
                    "status": "growing / stable / declining / changing / unverified",
                    "assessment": "Explanation of momentum",
                    "historical_comparison": "Earlier versus recent activity"
                }},
                "key_figures": [
                    {{
                        "name": "Person's name",
                        "field": "Area of activity",
                        "industry": "Verified industry or empty string",
                        "profession": "Verified profession or empty string",
                        "photo_url": "",
                        "photo_source_url": "",
                        "connection": "Documented relationship to the topic",
                        "significance": "Why this person matters",
                        "source_urls": [],
                        "supporting_work": [
                            {{
                                "title": "Actual title of the work, project, series, or source article",
                                "url": "https://..."
                            }}
                        ]
                    }}
                ],
                "cultural_significance": "Why the phenomenon matters",
                "commercial_signals": "Brief synthesis followed by Markdown bullets of named, directly linked commercial examples and what each demonstrates",
                "commercial_potential": "Evidence-based interpretation",
                "related_communities": [
                    {{
                        "name": "Verified relevant community name",
                        "platform": "Platform or community website",
                        "description": "Why the community is relevant to the finding",
                        "url": "https://..."
                    }}
                ],
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
    - related_communities is displayed as Relevant communities. Return
      named communities with a verified direct URL to their actual home,
      official join page, subreddit, or forum and explain their relevance.
      Do not provide guessed invites, generic platform homepages, or search
      URLs. Return [] if no relevant community location can be verified.
    - Return actual values, not the placeholder examples.
    - Keep summary to 1-2 concise sentences about the findings'
      substantive insights, not their titles or a topic inventory.
    - Use an empty list when no verified key figures exist.
    - For each key figure, give supporting_work links their actual work,
      project, series, or article title, not generic labels like "Supporting
      source". A work title must link to that work or a source specifically
      about it; do not label an unrelated article as the work itself.
      Keep source_urls for additional provenance. Use [] for supporting_work
      if no named work or article can be verified. Include industry and
      profession only when supported. photo_url is optional: use a verified
      direct image URL depicting that figure with a photo_source_url credit;
      leave both empty if unavailable. Never guess a portrait URL or identity.
    - Do not invent evidence to complete a field.
    - Explain uncertainty explicitly.
    - Separate documented commercial signals
      from speculative commercial potential.
    - commercial_signals must list verified named examples with direct
      Markdown links, not just categories such as merchandise or events.
      Keep this field a string. If none can be verified, state that plainly.
    - Include source URLs supporting important claims.
    - Do not use a numerical opportunity score.
    - Preserve engagement as a readable summary. Supplement it with
      engagement_evidence entries only for documented activities with direct
      source URLs. Return [] when none can be substantiated.
    - Write audience groups as an explicit numbered list (1), (2), etc.
      Use a short group name followed by a colon and its full explanation.
      Also provide audience_groups for consistent audience blocks. Use the
      same names in audience, audience_groups and audience_communities.
      Every group needs direct supporting source_urls. Examples must have
      real names, specific explanations and direct URLs; return [] for
      examples when none can be verified. Prefer several well-supported,
      distinct examples over repeating generic audience descriptions.
      audience_communities maps those same group names to verified gathering
      places; do not add unsupported groups to populate the visualization.
      Each entry needs the real community URL and an evidence_url supporting
      the described connection. Return [] when none can be verified.
      Optional audience community metrics follow the same sourced, verified
      metric fields below. Label membership, online counts and activity
      separately; do not equate a community's membership with audience size.
    - evidence_type must be exactly event, project, publication, or community.
      Classify a creator by the specific documented activity, not fame alone.
    - metrics is optional and defaults to []. Include a metric only when its
      numeric value, unit and date or period are explicitly verified in the
      linked source. Never invent, estimate, use placeholder numbers, or turn
      missing data into zero. Omit unverified metrics entirely.
    - Each metric uses these fields: name (precise measurement definition),
      value (actual JSON number), unit, period, source_url, verified (true only
      after checking the source). Include counting scope and qualifiers in
      the evidence description. Do not confuse reach with active engagement.
    - For genuinely comparable metrics only, also provide comparison_group
      (shared definition, platform, population/scope and methodology),
      measurement_basis (e.g. cumulative total or count during period), and
      period_kind (snapshot, daily, monthly, or annual). Use ISO period values:
      YYYY-MM-DD for snapshots/daily, YYYY-MM for monthly, YYYY for annual.
      Preserve other source periods as text without comparison fields when
      they cannot be represented faithfully. Never force comparability.
    - Historical metrics must describe the same entity, measurement, unit,
      scope, counting method and period type at each documented time point.
      Distinguish cumulative totals from interval counts. Do not duplicate
      measurements or extrapolate historical values.
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
    max_output_tokens=MAX_OUTPUT_TOKENS,
    include=["web_search_call.action.sources"],
)

    # ----------------------------------------------
    # PARSE JSON
    # ----------------------------------------------

    raw_text = response.output_text or ""


    # Check whether the research response completed.
    check_response_complete(response, "research")

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
            max_output_tokens=MAX_OUTPUT_TOKENS
        )

        check_response_complete(formatting_response, "JSON formatting")

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
