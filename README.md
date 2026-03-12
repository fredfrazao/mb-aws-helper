# AWS Helper – Artifactory & GitLab Tools

A modular Python helper for AWS operations around Artifactory and GitLab.

# homebrew-mb-aws-helper

Homebrew tap for mb-aws-helper.

## Install

```bash
brew tap fredfrazao/mb-aws-helper
brew install mb-aws-helper


# update
brew update
brew untap fredfrazao/mb-aws-helper 2>/dev/null || true
brew tap fredfrazao/mb-aws-helper
brew reinstall mb-aws-helper
mb-aws-helper --help
```

It supports:

- service selection for `artifactory` and `gitlab`
- environment selection for `sandbox`, `int`, and `prod`
- AWS profile export generation
- Auto Scaling Group discovery
- EC2 instance discovery from ASGs
- interactive SSM shell sessions
- Artifactory support bundle execution and status tracking through SSM
- GitLab deploy-node listing and screen-based session opening
- opening a shell on the first GitLab rails-worker instance
- interactive menu mode when no CLI arguments are provided
- short in-memory discovery cache to reduce repeated AWS calls during quick navigation
- environment summary output for fast operational checks

## Requirements

- Python 3.8+
- AWS CLI installed and available in `PATH`
- `granted` installed and configured for AWS SSO
- AWS profiles matching the expected naming convention
- access to the required AWS accounts
- `boto3` and `botocore`


## Project structure

```text
.
├── aws-helper                  # convenience wrapper
├── aws_tool.py                 # compatibility wrapper / entrypoint
├── README.md
├── requirements.txt
├── init.sh
└── aws_helper
    ├── __init__.py
    ├── main.py
    ├── constants.py
    ├── validators.py
    ├── selection.py
    ├── aws
    │   ├── auth.py
    │   ├── cache.py
    │   └── discovery.py
    ├── cli
    │   └── parser.py
    ├── commands
    │   ├── artifactory.py
    │   ├── common.py
    │   └── gitlab.py
    ├── interactive
    │   └── menu.py
    ├── output
    │   └── renderers.py
    ├── ssm
    │   └── session.py
    └── utils
        ├── common.py
        └── logging_utils.py
```

## Profile resolution

The tool builds the AWS profile name from the selected service and environment.

Environment mapping:

- `prod` → `PROD`
- `sandbox` → `DEV`
- `dev` → `DEV`
- `int` → `INT`
- `integration` → `INT`

Profile patterns:

- Artifactory: `setart_SWFCS---SETART---Artifactory-{suffix}/1238-SwfDev`
- GitLab: `setart_SWFCS---SETART---Gitlab-{suffix}/1238-SwfDev`

Examples:

- `env=sandbox`, `service=artifactory` → `setart_SWFCS---SETART---Artifactory-DEV/1238-SwfDev`
- `env=prod`, `service=gitlab` → `setart_SWFCS---SETART---Gitlab-PROD/1238-SwfDev`

## Authentication behavior

The tool uses `boto3` with the resolved AWS profile.

When credentials are missing or expired, it attempts to run:

```bash
granted sso login --sso-start-url https://mb001.awsapps.com/start --sso-region eu-central-1
```

If `granted` is not installed or login fails, the command exits with an error.

## Interactive mode

Run with no arguments:

```bash
python aws_tool.py
```

or:

```bash
./aws-helper
```

Interactive mode lets you:

- choose the service
- choose the environment
- list ASGs
- list instances
- open SSM sessions
- run or watch Artifactory support bundles
- work with GitLab deploy nodes
- open a rails-worker shell
- show an environment summary
- navigate back to previous menus or exit

### Interactive actions

Common actions:

```text
1) Set AWS env (env)
2) List ASGs
3) List instances
4) SSM session (select)
5) SSM session by instance-id
6) Environment summary
```

Artifactory actions add:

```text
7) Run support bundle (jfrog_support_collect.sh)
8) Watch support bundle status
```

GitLab actions add:

```text
7) List GitLab deploy nodes
8) GitLab deploy node (new screen session)
9) GitLab deploy node (recover screen session)
10) GitLab rails-worker shell (first instance)
```

## CLI overview

Global options:

```bash
python aws_tool.py --region eu-central-1 --verbose <command>
python aws_tool.py --region eu-central-1 --debug <command>
```

Top-level commands:

- `env`
- `asgs`
- `instances`
- `summary`
- `support`
- `ssm`
- `deploy-node`
- `rails-worker-shell`

## Alias and command mapping

This section is intended for direct inclusion in other docs or internal README sections.

```markdown
### Command aliases / quick map

- `env` → print shell exports for AWS profile and region
- `asgs` → list Auto Scaling Groups
- `instances` → list EC2 instances discovered from ASGs
- `summary` → show a quick environment summary
- `support instances` → run `jfrog_support_collect.sh` through SSM on Artifactory targets
- `support status` → inspect an SSM command status for Artifactory support bundle runs
- `ssm` → open an interactive SSM shell session
- `deploy-node list` → list GitLab deploy-node instances
- `deploy-node open new` → open GitLab deploy node and start a new `screen` session
- `deploy-node open recover` → open GitLab deploy node and recover/attach to an existing `screen` session
- `rails-worker-shell` → open a shell on the first matching GitLab rails-worker instance
```

## CLI examples

### Print AWS environment exports

```bash
python aws_tool.py env sandbox
python aws_tool.py env prod --service gitlab
```

Use with `eval`:

```bash
eval "$(python aws_tool.py env sandbox)"
eval "$(python aws_tool.py env prod --service gitlab)"
```

### List ASGs

```bash
python aws_tool.py asgs sandbox
python aws_tool.py asgs sandbox --service gitlab
python aws_tool.py asgs prod --service gitlab --asg deploy
python aws_tool.py asgs int --json
```

### List instances

```bash
python aws_tool.py instances prod
python aws_tool.py instances int --service gitlab
python aws_tool.py instances sandbox --service gitlab --state running
python aws_tool.py instances sandbox --service gitlab --asg rails-worker
python aws_tool.py instances sandbox --match i-0123456789abcdef0
python aws_tool.py instances sandbox --sort desc --json
```

### Environment summary

```bash
python aws_tool.py summary sandbox
python aws_tool.py summary prod --service gitlab
python aws_tool.py summary prod --service gitlab --asg deploy --json
```

The summary includes:

- number of ASGs
- total instances
- count by inferred role
- distribution by AZ
- instance types in use
- AMIs in use
- deploy-node count

### Open SSM session

```bash
python aws_tool.py ssm sandbox
python aws_tool.py ssm prod --service gitlab
python aws_tool.py ssm sandbox --instance-id i-0123456789abcdef0
python aws_tool.py ssm sandbox --service gitlab --asg rails-worker
```

### Artifactory support bundle

```bash
python aws_tool.py support instances prod 12345 24h
python aws_tool.py support instances prod 12345 24h --asg worker --no-dry-run
python aws_tool.py support status prod 12345678-aaaa-bbbb-cccc-1234567890ab
python aws_tool.py support status prod 12345678-aaaa-bbbb-cccc-1234567890ab --watch
```

### GitLab deploy nodes

```bash
python aws_tool.py deploy-node list sandbox
python aws_tool.py deploy-node list prod --asg deploy
python aws_tool.py deploy-node open sandbox new
python aws_tool.py deploy-node open sandbox recover
python aws_tool.py deploy-node open prod new --instance-id i-0123456789abcdef0
```

### GitLab rails-worker shell

```bash
python aws_tool.py rails-worker-shell sandbox
python aws_tool.py rails-worker-shell prod --asg rails-worker
```

## Discovery cache

The refactor adds a small in-memory discovery cache with a short TTL.

Purpose:

- speed up repeated menu actions
- reduce repeated AWS API calls
- make back-to-back instance/ASG navigation feel faster

Notes:

- cache is process-local
- default TTL is 30 seconds
- a new process starts with an empty cache

## Troubleshooting

### `granted` not found

Install and configure `granted`, then retry.

### AWS profile not found

Confirm the expected profile exists locally and matches the generated naming pattern.

### No command invocations found

Make sure the same region and AWS profile are being used as when the command was sent.

### `aws` CLI not found

Install AWS CLI and ensure it is available in `PATH`.

### Empty results for GitLab or Artifactory filters

Check:

- correct environment
- correct region
- ASG naming conventions
- whether instances are in `running` state where required

## Validation checklist

Use these checks after the refactor:

```bash
python -m compileall aws_helper aws_tool.py
python aws_tool.py --help
python aws_tool.py env sandbox
python aws_tool.py asgs sandbox --service artifactory
python aws_tool.py instances sandbox --service gitlab --json
python aws_tool.py summary sandbox --service gitlab
```

Interactive smoke test:

```bash
python aws_tool.py
```

Validate manually:

- service selection still works
- environment selection still works
- menu navigation works
- SSM session selection still works
- Artifactory support bundle flow still works
- GitLab deploy-node flows still work
- rails-worker shell still opens the first matching node

## Future-safe extension points

The new structure makes it easier to add:

- more GitLab-specific operations
- more Artifactory administrative helpers
- richer filtering
- better output formats
- unit tests per module
- command aliases or shell completions

## Homebrew packaging notes

This repository includes:

- `mb-aws-helper` as the preferred user-facing wrapper
- `scripts/build-release.sh` to create a Homebrew-friendly tarball
- `scripts/upload-r2.sh` to upload the tarball to Cloudflare R2
- `.github/workflows/release.yml` to build a release on tag push, publish a GitHub Release, optionally upload to R2, and optionally update a Homebrew tap repository

Typical release flow:

```bash
./scripts/build-release.sh 1.0.0
```

That produces:

- `dist/mb-aws-helper-1.0.0.tar.gz`
- `dist/mb-aws-helper-1.0.0.sha256`

The Homebrew tap formula should point to a public URL for the tarball and use the SHA256 from the generated file.
