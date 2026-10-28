#!/usr/bin/env python3
"""Dependency-free BountyHunter opportunity triage workflow."""
import argparse
import json
import re
import urllib.request
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


def normalize_opportunity(raw):
    item = dict(raw or {})
    item["name"] = str(item.get("name") or item.get("title") or "Untitled opportunity").strip()
    item["type"] = str(item.get("type") or "other").strip().lower()
    item["url"] = str(item.get("url") or item.get("source_url") or "").strip()
    item["deadline"] = str(item.get("deadline") or "").strip()
    item["interests"] = [str(x).strip().lower() for x in item.get("interests", []) if str(x).strip()]
    item["eligibility"] = dict(item.get("eligibility") or {})
    return item


def canonical_url(url):
    if not url:
        return ""
    p = urlsplit(url.strip())
    if p.scheme and p.netloc:
        return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/"), "", ""))
    return url.strip().rstrip("/")


def deduplicate_by_url(records):
    unique, seen = [], set()
    for raw in records:
        item = normalize_opportunity(raw)
        key = canonical_url(item["url"])
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        unique.append(item)
    return unique


def evaluate_opportunity(candidate, opportunity, today=None):
    today = today or date.today()
    candidate = candidate or {}
    eligibility = opportunity.get("eligibility") or {}
    reasons, conflicts, missing = [], [], []

    countries = eligibility.get("countries")
    if countries:
        country = str(candidate.get("country") or "").strip().casefold()
        if not country:
            missing.append("Candidate country is missing; verify location eligibility.")
        elif country not in [str(c).strip().casefold() for c in countries]:
            conflicts.append(f"Candidate country does not match eligible countries ({', '.join(map(str, countries))}).")
        else:
            reasons.append("Candidate country matches a listed eligible country.")
    else:
        missing.append("Country eligibility is not specified; verify official requirements.")

    age_requirements = [(key, eligibility.get(key)) for key in ("min_age", "max_age") if eligibility.get(key) is not None]
    if age_requirements:
        age = candidate.get("age")
        if age is None or str(age).strip() == "":
            missing.append("Candidate age is missing; verify age requirements.")
        else:
            try:
                age = int(age)
                if eligibility.get("min_age") is not None and age < int(eligibility["min_age"]):
                    conflicts.append(f"Candidate is below minimum age ({eligibility['min_age']}).")
                if eligibility.get("max_age") is not None and age > int(eligibility["max_age"]):
                    conflicts.append(f"Candidate is above maximum age ({eligibility['max_age']}).")
                if not conflicts:
                    reasons.append("Candidate age meets listed age requirements.")
            except (ValueError, TypeError):
                missing.append("Candidate age is not a valid number; verify age requirements.")

    if conflicts:
        status = "Not eligible"
        reasons = conflicts + reasons
    elif missing:
        status = "Needs verification"
        reasons = missing + reasons
    else:
        status = "Potential match"
        reasons = reasons or ["All stated eligibility requirements were evaluated; confirm with the official source."]

    deadline = opportunity.get("deadline", "")
    expired, urgency, days_left = False, "No deadline", None
    if deadline:
        try:
            deadline_date = date.fromisoformat(str(deadline)[:10])
            days_left = (deadline_date - today).days
            expired = days_left < 0
            if expired:
                urgency = "Expired"
            elif days_left <= 3:
                urgency = "Closing soon"
            elif days_left <= 14:
                urgency = "Coming up"
            else:
                urgency = "Upcoming"
        except ValueError:
            urgency = "Verify deadline"
    return {"eligibility_status": status, "eligibility_reasons": reasons,
            "expired": expired, "urgency": urgency, "days_left": days_left}


def build_report(candidate, records, today=None):
    today = today or date.today()
    candidate = candidate or {}
    interests = {str(x).strip().casefold() for x in candidate.get("interests", []) if str(x).strip()}
    evaluated = []
    for item in deduplicate_by_url(records):
        matched = sorted(interests.intersection({x.casefold() for x in item.get("interests", [])}))
        result = dict(item)
        result["matched_interests"] = matched
        result["interest_score"] = len(matched)
        result.update(evaluate_opportunity(candidate, item, today))
        result["rank_score"] = result["interest_score"] * 100 + (max(0, 30 - result["days_left"]) if result["days_left"] is not None and not result["expired"] else 0)
        evaluated.append(result)
    evaluated.sort(key=lambda x: (-x["rank_score"], x["name"].casefold()))
    return {"generated_on": today.isoformat(), "opportunities": evaluated}


def fetch_page_title(url):
    """Best-effort title extraction only; never an eligibility verification."""
    request = urllib.request.Request(url, headers={"User-Agent": "BountyHunter/1.0 (user-requested title extraction)"})
    with urllib.request.urlopen(request, timeout=8) as response:
        content = response.read(500_000).decode("utf-8", "replace")
    match = re.search(r"<title[^>]*>(.*?)</title\s*>", content, re.I | re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", match.group(1))).strip() if match else ""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, help="Candidate profile JSON file")
    parser.add_argument("--opportunities", required=True, help="Opportunity array JSON file")
    parser.add_argument("--output", required=True, help="Report JSON destination")
    args = parser.parse_args()
    candidate = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    opportunities = json.loads(Path(args.opportunities).read_text(encoding="utf-8"))
    report = build_report(candidate, opportunities)
    Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(report['opportunities'])} opportunities to {args.output}")


if __name__ == "__main__":
    main()
