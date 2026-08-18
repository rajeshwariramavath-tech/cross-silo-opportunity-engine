# Cross-silo opportunity engine
*Architecture and end-to-end flow*
---

## The problem

Commercial real estate firms are typically organized into separate lines of business —
brokerage, financing, valuation, property management — each running its own systems, its own
data model, and its own definition of a "client" or a "property." These systems rarely talk to
each other. As a result, information that would be valuable across the firm often stays locked
inside the team that generated it: a relationship one team has with a client isn't visible to
another team that could act on it, and a signal that emerges in one system's data goes unseen
by the teams positioned to respond to it. The result is missed business — not because the firm
lacks the underlying information, but because that information is fragmented across systems
that were never designed to connect. The core question this project answers is: how do you
connect data across siloed lines of business so opportunities like that surface automatically,
without giving everyone unrestricted access to sensitive data they shouldn't see.

---

## Stage 1 — Ingestion & normalization

### Why this stage exists

Records from different source systems describe the same real-world things in different words —
different address formats, different name abbreviations, no shared identifier between systems.
Before anything else can happen — before we can even ask "are these the same entity?" — every
source needs to be rewritten into one common format the rest of the pipeline understands. Think
of it as a translator: each source system speaks its own dialect, and this stage translates
everything into one shared language.

### What actually happens

One small adapter per source system. Each adapter's only job is to read its own system's native
format and rewrite each record into a canonical (shared) shape: normalizing addresses (case,
common abbreviations, stripping suite/floor into their own fields), normalizing entity names,
and validating that required fields are present before anything moves downstream. Invalid
records are flagged and logged rather than silently dropped or silently passed through.

Every canonical record also carries "where did this come from" metadata — its source system and
its original record ID. This is easy to overlook but is what makes lineage, and therefore
governance, possible later. Paying for it here means it doesn't have to be reconstructed
downstream.

---

## Stage 2 — Entity resolution

### Why this stage exists

Once records are in a common shape, the real question can be asked: do two records from
different systems describe the same underlying entity? There's no shared ID to look up — that
identity has to be inferred from the content of the records themselves. And it's rarely
black-and-white: some pairs clearly match, some clearly don't, and some sit in an ambiguous
middle where the signals disagree slightly. Getting this wrong in either direction — false
match or false non-match — means every downstream stage produces a wrong answer, so this stage
has to be both careful and honest about its own uncertainty.

### What actually happens

Candidate record pairs are compared across several independent signals — typically normalized
address similarity, normalized name similarity, and optionally geographic proximity. Those
signal scores are combined into a single confidence score (a weighted combination, with weights
chosen based on which signal is more reliable), and the result is sorted into one of three
outcomes rather than forced into a binary decision:

- **Auto-match** — confidence high enough to link automatically.
- **Review queue** — confidence in an ambiguous middle range; sent to a human rather than guessed.
- **Auto-reject** — confidence too low to be the same entity.

The three-outcome approach is the key design decision here. A single threshold forcing a
yes/no answer means the system silently guesses on ambiguous cases; the three-outcome approach
makes that uncertainty visible instead of hidden, and routes it to a human where it belongs.

---

## Stage 3 — Opportunity detection

### Why this stage exists

A linked pair of records isn't automatically a business opportunity — most links are just "we
now know these two records describe the same thing," not "someone should act on this today."
This stage decides which resolved matches represent a real, timely opportunity worth surfacing
to a person, and ranks them so the most valuable ones surface first.

### What actually happens

Resolved matches are run through explicit, deterministic business rules — not a machine
learning model, deliberately, because rules are auditable. If someone later asks "why did the
system flag this?", the answer is the exact condition that fired, not an opaque score. Rules
combine factors like timing/urgency, a minimum value threshold, and evidence of an existing
relationship, and qualifying records are ranked by a composite of those factors.

An optional LLM step can follow the rules to write a short, plain-language explanation of *why*
a given record was flagged — but it only explains a decision the rules already made, grounded
strictly in that record's own fields. It never makes the underlying business decision itself;
that separation is what keeps the system auditable in a regulated, relationship-driven business.

---

## Stage 4 — Governance & access control

### Why this stage exists

Everything up to this point has been about combining data across systems. This last stage is
about deciding who is allowed to see the result, and how much of it. An opportunity record can
combine information from multiple sides of the business, some of it sensitive. Without an
explicit governance layer, a pipeline like this either leaks sensitive information to people who
shouldn't see it, or gets locked down so tightly it stops being useful to anyone. Neither is
acceptable.

Governance isn't only about the final delivery step, either — lineage captured all the way back
at ingestion is what makes it possible to answer "where did this number come from?" later,
tracing any field in the final output back to its original source record.

### What actually happens

When a user requests results, the pipeline checks that user's role and applies scoping rules
before returning anything — the same underlying opportunity is rendered differently depending on
who's asking, from a full record with complete detail down to a minimal flag with sensitive
terms withheld, based on a role-to-field-permissions mapping defined once and applied
consistently at every request.

---

## Putting it all together

Records enter the pipeline in whatever messy, inconsistent shape their source system produced
them in, with no shared identifier connecting them across systems. Ingestion rewrites them into
one canonical shape. Entity resolution scores their similarity and either links them
automatically, rejects them, or routes the ambiguous cases to a human. Opportunity detection
applies auditable rules to the resolved matches, ranks the results, and can optionally attach a
grounded, plain-language explanation. Governance then scopes what gets delivered based on the
requesting user's role, with every field traceable back to the exact source record it came from.

Each stage exists because the previous stage's output isn't yet useful on its own, and the next
stage can't do its job without it.

## What I'd build next

The most concrete extension of this architecture is a land-parcel discovery pipeline for an
emerging asset class such as data centers. That sector has become one of the most active areas
of commercial real estate activity, driven by a genuine land rush — developers and operators are
racing to secure sites with the specific combination of power availability, fiber access, water,
and zoning that this kind of development requires, and suitable parcels are becoming scarce
faster than firms can identify them internally. An internal parcel database only captures what a
firm already knows about or has been offered; it doesn't surface parcels that meet the criteria
but haven't crossed the firm's desk yet.

This pipeline would apply the same four-stage shape used here to a different pairing of
sources: an internal parcel database matched against public government and county zoning
records, GIS data, and utility infrastructure filings. Ingestion would normalize parcel
identifiers and zoning codes across those sources the same way records are normalized here.
Entity resolution would match parcels by geographic overlap and legal description rather than
by address string similarity, since public zoning records often use plat and lot numbers
instead of street addresses. Opportunity detection would apply rules specific to this use case —
minimum parcel size, zoning designation, proximity to power substations and fiber routes,
availability status — to rank parcels worth pursuing. Governance would still apply, scoping
which internal teams see raw parcel data versus a filtered shortlist.

The point of describing rather than building this: the underlying architecture doesn't change
to support it, only the source adapters and the domain-specific rules in stage 3 do. That's the
strongest evidence that the pattern built here generalizes beyond the one opportunity type it
was built and tested against.
