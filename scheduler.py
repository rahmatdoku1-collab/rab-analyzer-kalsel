from apscheduler.schedulers.background import BackgroundScheduler
import time

_scheduler = None


def _safe_run(fn):
    try:
        fn()
    except Exception as e:
        print(f"[scheduler] {fn.__name__} error: {e}")


def start_scheduler():
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    print("[scheduler] Starting background scheduler...")
    _scheduler = BackgroundScheduler(daemon=True, timezone="Asia/Makassar")

    from news_agent import run_news_agent
    from crawler import run_crawlers
    from pricing_engine import update_rolling_averages

    # News agent — every 2 hours
    _scheduler.add_job(
        lambda: _safe_run(run_news_agent),
        "interval", hours=2, id="news_agent",
        misfire_grace_time=300,
    )
    # Price crawler — every 6 hours
    _scheduler.add_job(
        lambda: _safe_run(run_crawlers),
        "interval", hours=6, id="crawler",
        misfire_grace_time=300,
    )
    # Rolling average pricing — daily at 01:00 WITA
    _scheduler.add_job(
        lambda: _safe_run(update_rolling_averages),
        "cron", hour=1, minute=0, id="pricing_engine",
        misfire_grace_time=600,
    )

    _scheduler.start()
    print("[scheduler] Started. Jobs: news(2h), crawler(6h), pricing(01:00 WITA).")
    return _scheduler


if __name__ == "__main__":
    start_scheduler()
    while True:
        time.sleep(60)
