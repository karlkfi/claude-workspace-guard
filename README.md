# workspace-guard

**This repository is archived and read-only. workspace-guard now ships from
[karlkfi/claude-bouncer](https://github.com/karlkfi/claude-bouncer).**

```
/plugin marketplace add karlkfi/claude-bouncer
/plugin install workspace-guard@claude-bouncer
```

Those two lines replace the pair this repo used to document. The plugin itself
did not change — same hook, same `WORKSPACE_GUARD_*` environment variables, same
`WORKSPACE_GUARD_OVERRIDE=<reason>` prefix, same
`/workspace-guard:friction-report`, same `reduce-workspace-guard-prompts` skill.
Nothing in your own repo needs editing.

The five guards — `workspace-guard`, `branch-guard`, `prod-guard`,
`exit-status-guard`, `foreground-guard` — all parse the same Bash command
strings, and were re-implementing that parser five times over. They share one
now, so they share a repository, a test suite, and a release pipeline.

## Where the docs went

[`plugins/workspace-guard`](https://github.com/karlkfi/claude-bouncer/tree/main/plugins/workspace-guard)
in claude-bouncer: decision table, guarded commands, the PowerShell and native
file-tool frontends, configuration reference, limitations, friction report.

Read that rather than anything in this repo. The last release here was `v1.10.0`
and the copy in claude-bouncer is ahead of it, so the pages under `docs/` here
describe behavior the shipping plugin no longer has. Since v1.10.0 the boundary
has moved outward: `cut`, `base64`, `unlink` and `ln` became guarded commands, a
write into another session's scratchpad now denies instead of prompting, and a
guarded read hidden inside a `case` clause or a heredoc is read in full instead
of escaping the scan.

## Switching an existing install

The marketplace name changes from `workspace-guard` to `claude-bouncer`, so an
existing install has to be removed and re-added — an update will not cross that
boundary, and the old marketplace still clones fine, so nothing tells you it has
gone quiet:

```
claude plugin uninstall workspace-guard@workspace-guard
claude plugin marketplace remove workspace-guard
claude plugin marketplace add karlkfi/claude-bouncer
claude plugin install workspace-guard@claude-bouncer
```

Restart Claude Code (or `/reload-plugins`) to apply. The `/plugin` menu does the
same four steps interactively, on the CLI, the IDE extensions, and Claude Code
for Claude Desktop.

**Repoint auto-update too.** If you followed the old install instructions you
have an `extraKnownMarketplaces` entry in `~/.claude/settings.json` naming this
repository, and it will go on refreshing a marketplace that will never publish
another release. Replace it:

```json
{
  "extraKnownMarketplaces": {
    "claude-bouncer": {
      "source": { "source": "git", "url": "https://github.com/karlkfi/claude-bouncer.git" },
      "autoUpdate": true
    }
  }
}
```

Any `WORKSPACE_GUARD_*` settings you keep beside it are read at hook time and
carry over untouched.

The four sibling guards are one `install` line each against that same
marketplace — see the
[claude-bouncer README](https://github.com/karlkfi/claude-bouncer#install).

## What is still here

History, and the links that point into it. Archiving keeps every issue, pull
request and tag resolving; it does not delete them. New issues and pull requests
belong on
[claude-bouncer](https://github.com/karlkfi/claude-bouncer/issues). The
pre-move documentation is readable at the
[`v1.10.0`](https://github.com/karlkfi/claude-workspace-guard/tree/v1.10.0) tag.

## License

[MIT](LICENSE)
