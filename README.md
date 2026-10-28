# BountyHunter

A dependency-free hackathon MVP for discovery and triage of hackathons, grants and internships. Runs as a static single-page interface; the optional Python backend serves the page on localhost and can extract a title from a user-supplied URL.

## Run

Requires Python 3 (standard library only).

```sh
cd /home/node/bountyhunter
python3 server.py
```

Open **http://127.0.0.1:8765**. The server binds only to loopback; it is not publicly exposed. The app's profile, shortlist and user-added opportunities are stored in this browser's localStorage. “Clear” removes the profile; browser storage can be cleared in browser settings.

### Workflow JSON report

Candidate JSON example:

```json
{"age": 21, "country": "Canada", "interests": ["climate", "design"]}
```

Use an opportunities JSON array and invoke:

```sh
python3 workflow.py --candidate candidate.json --opportunities opportunities.json --output report.json
```

The report normalizes fields, deduplicates canonical URLs (first record wins), evaluates only stated country and age requirements, and ranks by interest overlap and remaining deadline time. Unknown requirements or missing candidate fields yield **Needs verification**; a known mismatch yields **Not eligible**. A result of **Potential match** covers only the explicit checks that were present and is not an official determination.

## Demo

1. Start the server and open the local preview. Three fictional opportunities are shown, one per type; each is marked **DEMO DATA, NOT VERIFIED LIVE**. Placeholder `.invalid` URLs are intentional and do not lead to real opportunities.
2. Try **Hackathons / Grants / Internships** filters.
3. Enter a country such as `Canada`, age `22`, and interests `climate, community`, then save; see deterministic statuses and ranking update.
4. Shortlist a card and export JSON. Both shortlist and profile persist in localStorage.
5. Paste an opportunity object/array or add an official URL. Title reading is best effort and title text is not used as eligibility evidence.
6. The visible notice states that no applications are submitted.

## Limitations and safety

- No paid APIs, third-party analytics, accounts, remote database, or application submission.
- Demo data is fictional and is explicitly labeled not verified live; deadlines are fictional sample values, not claims about real programs.
- Eligibility checks intentionally use only structured `eligibility.countries`, `min_age`, and `max_age` input. They do not assess citizenship, residency, education, work authorization, or any unprovided terms. `Potential match` is not a guarantee.
- Deadline ranking is a lightweight heuristic, based on date strings in `YYYY-MM-DD` format. Verify deadlines, time zones, eligibility and all other terms on official sources.
- URL title extraction is optional, best effort, and may fail for inaccessible/dynamic pages. It extracts only a title, not complete page contents or verified requirements. The URL is user-supplied; only use trusted sources.
- LocalStorage is per-browser/device, not encrypted or synced. Candidate profile is empty by default.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

Covers unknown country, country mismatch, missing age, expired deadline, duplicate URL handling, and normalized report ranking.

## Build provenance

Built in-session by the Agent37-hosted Hermes Agent from the user-provided specification, using local file and Python standard-library tools. No personal accounts, paid APIs, external publication, deployment or submission were used. The local preview is bound to `127.0.0.1` only. No schedules were enabled.
