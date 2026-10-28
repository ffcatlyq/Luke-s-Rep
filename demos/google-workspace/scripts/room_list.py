"""
列出域内 calendar resources（会议室 / 设备），按 site 前缀过滤。

用法:
  python3 room_list.py                        # 全部，stdout 摘要
  python3 room_list.py --prefix RSH           # 只列上海
  python3 room_list.py --prefix RSH --csv rooms.csv
  python3 room_list.py --building CRMS_609    # 按 buildingId 过滤
"""
import argparse
import csv
import sys

from gw_client import get_admin_directory_service


def fetch_all():
    svc = get_admin_directory_service()
    items = []
    page = None
    while True:
        resp = svc.resources().calendars().list(
            customer="my_customer", maxResults=500, pageToken=page
        ).execute()
        items.extend(resp.get("items", []))
        page = resp.get("nextPageToken")
        if not page:
            break
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", help="过滤 generatedResourceName 前缀，如 RSH (Shanghai)")
    ap.add_argument("--building", help="过滤 buildingId，如 CRMS_609")
    ap.add_argument("--csv", help="写出 CSV 路径")
    args = ap.parse_args()

    items = fetch_all()
    print(f"Domain total: {len(items)}", file=sys.stderr)

    if args.prefix:
        items = [i for i in items if i.get("generatedResourceName", "").startswith(args.prefix + "-")]
    if args.building:
        items = [i for i in items if i.get("buildingId") == args.building]

    print(f"Filtered: {len(items)}", file=sys.stderr)

    rows = []
    for r in items:
        features = ", ".join(
            fi.get("feature", {}).get("name", "")
            for fi in (r.get("featureInstances") or [])
        )
        rows.append({
            "email": r.get("resourceEmail"),
            "name": r.get("generatedResourceName"),
            "short_name": r.get("resourceName"),
            "capacity": r.get("capacity"),
            "building": r.get("buildingId"),
            "floor": r.get("floorName"),
            "category": r.get("resourceCategory"),
            "features": features,
        })

    if args.csv:
        with open(args.csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader()
            w.writerows(rows)
        print(f"Wrote {len(rows)} rows to {args.csv}", file=sys.stderr)
    else:
        for r in rows:
            print(f"  cap={r['capacity'] or '?':>3} | {r['floor'] or '':<6} | {r['building'] or '':<10} | {r['name']}")


if __name__ == "__main__":
    main()
