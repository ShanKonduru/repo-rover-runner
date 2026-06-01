# Utility Script Help

This folder documents the root-level helper scripts shipped with Repo Rover Runner.

Each document covers both platform variants of the same utility:

- Windows: `.bat`
- Linux/macOS: `.sh`

Most helpers follow the same conventions:

- They look for `REPO_CONFIG_FILE` first.
- If `REPO_CONFIG_FILE` is not set, they choose a provider-specific env file based on `REPO_PROVIDER`.
- If neither is set, they prefer `repo_rover_runner.bitbucket.env`, then `repo_rover_runner.github.env`, then `repo_rover_runner.env`.
- They expect config values like `REPO_URL`, `LOCAL_REPO_PATH`, `TARGET_BRANCH`, `BASE_BRANCH`, and `REMOTE` depending on the operation.
- Several helpers clone the repository first if `LOCAL_REPO_PATH` does not already contain a `.git` directory.

Utility docs:

- [create_new_branch.md](create_new_branch.md)
- [install_dev_dependencies.md](install_dev_dependencies.md)
- [list_files_in_branch.md](list_files_in_branch.md)
- [run_bitbucket_connectivity.md](run_bitbucket_connectivity.md)
- [run_bitbucket_tests.md](run_bitbucket_tests.md)
- [run_github_connectivity.md](run_github_connectivity.md)
- [run_github_tests.md](run_github_tests.md)
- [run_repo_rover_runner_unit_tests.md](run_repo_rover_runner_unit_tests.md)
- [run_security_reports.md](run_security_reports.md)
- [test_list_branches.md](test_list_branches.md)
- [test_ping_repo.md](test_ping_repo.md)
- [test_push_dummy.md](test_push_dummy.md)
- [test_use_branch.md](test_use_branch.md)