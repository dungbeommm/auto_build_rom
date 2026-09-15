# Pre-run audit

## Fixed

- Correct repository-root ZIP layout and required-file preflight.
- APT disk exhaustion: cleanup, smaller indexes, no package cache, 8 GB root reserve.
- Removed interactive Android Image Tools dependency check from the build path; pipeline now calls native unpack/repack helpers directly.
- Added complete runtime dependency installation and command verification.
- Fixed patch report overwrite; results now accumulate by partition.
- Fixed system-app destination selection by active partition.
- Replaced shell-based plugin execution with checked subprocess execution.
- Fixed release part checksums and JOIN script paths.
- Added output existence checks before splitting and publishing.
- Added URL hostname boundary checks, port restriction, public-IP validation, HTTPS-only redirects and effective-URL validation.
- Added safe TAR traversal/link validation.
- Added download-size verification and disk-space preflight.
- Added clean workspace/output handling for reruns.
- Added support for logical partition names with `_a` suffix.
- Fixed packaging when a ROM archive has multiple top-level entries.
- Added unit tests, ShellCheck and actionlint validation.

## Verified

- Python syntax and four unit tests.
- Bash syntax and ShellCheck with zero findings.
- GitHub workflow actionlint with zero findings.
- Workflow YAML parsing.
- Feature report accumulation across multiple partitions.
- Unsafe TAR traversal rejection.
- Release split, checksum, join and final checksum round-trip.

## Remaining environmental risks

A complete 9.6 GB ROM build cannot be executed inside this small development sandbox. The workflow performs an early disk check on GitHub Actions. Some ROM releases may exceed the storage or six-hour limit of a standard hosted runner; that is a platform capacity limitation rather than a script error.
