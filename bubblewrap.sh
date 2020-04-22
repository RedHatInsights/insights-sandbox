#!/usr/bin/env bash
set -euo pipefail
#    --unshare-all                Unshare every namespace we support by default
#    --unshare-user               Create new user namespace (may be automatically implied if not setuid)
#    --unshare-user-try           Create new user namespace if possible else continue by skipping it
#    --unshare-ipc                Create new ipc namespace
#    --unshare-pid                Create new pid namespace
#    --unshare-net                Create new network namespace
#    --unshare-uts                Create new uts namespace
#    --unshare-cgroup             Create new cgroup namespace
#    --unshare-cgroup-try         Create new cgroup namespace if possible else continue by skipping it

# Unsharing pid ns means we need a pid 1 with something like tini.
# https://github.com/krallin/tini
# I'm inheriting the pid ns to simplify.

# TODO investigate unshare-cgroup
# TODO investigate unshare-user
(exec bwrap --ro-bind /usr /usr \
            --symlink usr/lib /lib \
            --symlink usr/lib64 /lib64 \
            --symlink usr/bin /bin \
            --symlink usr/sbin /sbin \
            --dev /dev \
            --bind /tmp /tmp \
            --bind $PWD $PWD \
            --chdir $PWD \
            --unshare-user \
            --unshare-ipc \
            --unshare-net \
            --unshare-uts \
            --die-with-parent \
            ./consumer.sh)
