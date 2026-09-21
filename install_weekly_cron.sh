#!/usr/bin/env bash
set -euo pipefail

# Install an idempotent Sunday 03:00 cron entry for the report generator.
# Run this as the Linux user whose Git credentials may push to the repository.

repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python_bin="$(command -v python3)"
script_path="${repo_dir}/nmap_scan_report.py"
log_path="${repo_dir}/nmap_scan_cron.log"
marker="# automated-nmap-report"
cron_entry="0 3 * * 0 cd '${repo_dir}' && '${python_bin}' '${script_path}' scanme.nmap.org --authorized >> '${log_path}' 2>&1 ${marker}"
report_branch="automated-scan-reports"

if ! command -v nmap >/dev/null 2>&1; then
    echo "Error: nmap is not installed or is not on PATH." >&2
    exit 1
fi

if ! command -v git >/dev/null 2>&1; then
    echo "Error: git is not installed or is not on PATH." >&2
    exit 1
fi

# Keep generated reports off protected main. Reuse the local or remote report
# branch when present; otherwise create it from the currently checked-out code.
if git -C "${repo_dir}" show-ref --verify --quiet "refs/heads/${report_branch}"; then
    git -C "${repo_dir}" switch "${report_branch}"
elif git -C "${repo_dir}" ls-remote --exit-code --heads origin "${report_branch}" >/dev/null 2>&1; then
    git -C "${repo_dir}" fetch origin "${report_branch}"
    git -C "${repo_dir}" switch --track -c "${report_branch}" "origin/${report_branch}"
else
    git -C "${repo_dir}" switch -c "${report_branch}"
    git -C "${repo_dir}" push -u origin "${report_branch}"
fi

existing_crontab="$(crontab -l 2>/dev/null || true)"
filtered_crontab="$(printf '%s\n' "${existing_crontab}" | grep -Fv "${marker}" || true)"

{
    printf '%s\n' "${filtered_crontab}"
    printf '%s\n' "${cron_entry}"
} | sed '/^[[:space:]]*$/d' | crontab -

echo "Installed weekly scan schedule:"
echo "${cron_entry}"
