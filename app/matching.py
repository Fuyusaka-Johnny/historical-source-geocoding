def match_locations(names, repository):
    groups = []
    for name in dict.fromkeys(names):
        rows, truncated = repository.candidates(name)
        candidates = []
        for row in rows:
            candidate = dict(row)
            for field in ("lat", "lng", "lat2", "lng2"):
                if candidate.get(field) is not None:
                    candidate[field] = float(candidate[field])
            candidates.append(candidate)
        groups.append({
            "query": name,
            "status": "unmatched" if not candidates else "needs_review",
            "candidate_count_returned": len(candidates),
            "truncated": truncated,
            "candidates": candidates,
            "selected_place_id": None,
        })
    return groups


def enrich(result, repository):
    names = [name for record in result["records"] for name in record["locations"]]
    groups = match_locations(names, repository)
    lookup = {group["query"]: group for group in groups}
    for record in result["records"]:
        record["location_matches"] = [lookup[name] for name in dict.fromkeys(record["locations"])]
    return {**result, "geocode_summary": groups}
