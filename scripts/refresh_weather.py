"""Manual cache warm-up for a public Indian location; no automatic cron required."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.services.providers import fetch_weather, ProviderError


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--latitude",type=float,required=True)
    p.add_argument("--longitude",type=float,required=True)
    p.add_argument("--start-year",type=int,default=2023)
    p.add_argument("--end-year",type=int,default=2023)
    args=p.parse_args()
    try:
        data,meta=fetch_weather(args.latitude,args.longitude,args.start_year,args.end_year)
    except ProviderError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Validated {len(data):,} hourly weather rows. Source: {meta['provider']} {meta['dataset']} | cache={meta['cache']}")

if __name__=="__main__":
    main()
