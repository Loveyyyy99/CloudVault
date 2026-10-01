"""Scheduled job (GitHub Actions cron): verify integrity, repair incomplete backups, print a health report."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import repo  # noqa: E402
from app.services import backup  # noqa: E402

VERIFY_LIMIT = int(os.getenv("VERIFY_LIMIT", "20"))


def main() -> int:
    providers = backup.build_providers(None)
    health = {n: p.health() for n, p in providers.items()}
    issues, repaired, unrecoverable = [], [], []

    if all(health.values()):
        for f in repo.files_to_verify(VERIFY_LIMIT):
            issues += backup.verify_file(f, providers)
        for f in repo.incomplete_files():
            try:
                status = backup.retry(f, providers)
                (repaired if status == "VERIFIED" else unrecoverable).append(f["filename"])
            except Exception as e:  # ApiError: no healthy source
                unrecoverable.append(f"{f['filename']} ({getattr(e, 'message', e)})")
    else:
        print("A cloud provider is unreachable — skipping repairs to avoid false failures.")

    lines = ["## CloudVault backup health report", "",
             f"- Backblaze B2: {'healthy' if health['b2'] else 'UNREACHABLE'}",
             f"- Supabase Storage: {'healthy' if health['supabase'] else 'UNREACHABLE'}",
             f"- Integrity issues found: {len(issues)}", f"- Repaired: {len(repaired)}",
             f"- Needs attention: {len(unrecoverable)}"]
    lines += [f"  - {i['file']} on {i['provider']}: {i['reason']}" for i in issues]
    lines += [f"  - {u}" for u in unrecoverable]
    report = "\n".join(lines)
    print(report)
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as fh:
            fh.write(report + "\n")
    return 0 if all(health.values()) and not unrecoverable else 1


if __name__ == "__main__":
    sys.exit(main())
