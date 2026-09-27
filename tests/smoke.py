#!/usr/bin/env python3
"""Exercise the copied starter against Docker using only disposable fixtures."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import urllib.request

STARTER = Path(__file__).resolve().parents[1]
LABEL = 'dev.agent-starter.task'


def run(*args, cwd=None, expected=0):
    result = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    assert result.returncode == expected, (args, result.returncode, result.stdout)
    return result.stdout


def resources(project):
    return ''.join(run('docker', *args, '--filter', f'label=com.docker.compose.project={project}')
                   for args in [('ps', '-aq'), ('volume', 'ls', '-q'), ('network', 'ls', '-q')])


def main():
    with tempfile.TemporaryDirectory(prefix='agent starter $ smoke-') as directory:
        root = Path(directory)
        repo = root / 'repo'
        shutil.copytree(STARTER, repo)
        # A .git pointer exercises the linked-worktree mount shape without
        # creating commits or changing the user's repositories.
        common = root / 'git-metadata'
        run('git', 'init', '--quiet', f'--separate-git-dir={common}', str(repo))
        run('git', '-C', str(repo), 'config', 'core.hooksPath', '/dev/null')
        (repo / '.env').write_text('PRIVATE_SENTINEL=must-not-be-visible\n')
        (repo / '.gitignore').write_text('.env\nnode_modules/\n.agent-data/\n')
        config_path = repo / '.devcontainer/project.json'
        config = json.loads(config_path.read_text())
        config.update(name=f'starter-smoke-{os.getpid()}', bootstrap=['true'], check=['true'], ports=[8080])
        config_path.write_text(json.dumps(config))
        launcher = str(repo / 'scripts/agent-container')
        run(launcher, 'build', cwd=repo)
        run(launcher, 'doctor', cwd=repo)
        print('PASS image build and non-root provider toolchain', flush=True)

        def task(*args, expected=0):
            output = run(launcher, *args, cwd=repo, expected=expected)
            project = re.search(r'Task project: (\S+)', output)
            assert project, output
            assert not resources(project[1]), output
            return output

        probe = r'''
set -eu
[ "$(id -u)" != 0 ]
[ ! -s /workspace/.env ]
[ ! -S /var/run/docker.sock ]
git status --short >/dev/null
if echo bad >> /workspace/.git 2>/dev/null; then exit 21; fi
common=$(git rev-parse --git-common-dir)
if touch "$common/should-not-exist" 2>/dev/null; then exit 22; fi
[ ! -e /workspace/node_modules/task-marker ]
touch /workspace/node_modules/task-marker
'''
        task('--sterile', 'exec', 'bash', '-c', probe)
        task('--sterile', 'exec', 'bash', '-c', probe)
        assert not (repo / 'node_modules/task-marker').exists()
        assert not (common / 'should-not-exist').exists()
        assert 'PRIVATE_SENTINEL' in (repo / '.env').read_text()
        task('--sterile', 'exec', 'bash', '-c', 'exit 37', expected=37)
        task('--sterile', 'check')
        print('PASS Git metadata, env masking, fresh volumes, failed-command status and cleanup', flush=True)

        auth = f'{config["name"]}-agent-codex-auth'
        try:
            task('codex', '--version')
            run('docker', 'volume', 'inspect', auth)
            task('--sterile', 'exec', 'bash', '-c', 'test -z "$(ls -A /home/dev/.codex)"')
            run('docker', 'volume', 'inspect', auth)
            print('PASS provider volume persistence and sterile exclusion', flush=True)
        finally:
            run('docker', 'volume', 'rm', auth)

        # Merge the supplied database example without resolving its per-task
        # environment yet. The runner resolves a fresh password for each task.
        compose = repo / '.devcontainer/compose.yaml'
        merged = run('docker', 'compose', '-f', str(compose), '-f',
                     str(repo / 'examples/postgres-redis.yaml'), 'config',
                     '--no-interpolate', '--format', 'json', cwd=repo)
        compose.write_text(merged)
        config['services'] = ['postgres', 'redis']
        config_path.write_text(json.dumps(config))

        # Start two servers simultaneously, then cancel their coordinators.
        active = []
        try:
            for index in range(2):
                log_path = root / f'task-{index}.log'
                log = log_path.open('w')
                process = subprocess.Popen([launcher, '--sterile', 'shell', '-c',
                    'exec python3 -m http.server 8080 --bind 0.0.0.0'], cwd=repo,
                    stdin=subprocess.DEVNULL, stdout=log, stderr=log)
                active.append((process, log, log_path))
            projects, ports = [], []
            for process, _, log_path in active:
                deadline = time.monotonic() + 90
                while time.monotonic() < deadline:
                    output = log_path.read_text()
                    match = re.search(r'Port 8080: http://127.0.0.1:(\d+)', output)
                    if match:
                        port = int(match[1])
                        try:
                            with urllib.request.urlopen(f'http://127.0.0.1:{port}', timeout=1) as response:
                                assert response.status == 200
                            break
                        except OSError:
                            pass
                    assert process.poll() is None, output
                    time.sleep(0.2)
                else:
                    raise AssertionError(log_path.read_text())
                projects.append(re.search(r'Task project: (\S+)', output)[1])
                ports.append(port)
            assert len(set(projects)) == len(set(ports)) == 2
            databases = [run('docker', 'ps', '-q', '--filter',
                            f'label=com.docker.compose.project={project}',
                            '--filter', 'label=com.docker.compose.service=postgres').strip()
                         for project in projects]
            assert all(databases) and len(set(databases)) == 2
            run('docker', 'exec', databases[0], 'psql', '-U', 'dev', '-d', 'app', '-c',
                'CREATE TABLE isolation_probe (id integer)')
            absent = run('docker', 'exec', databases[1], 'psql', '-U', 'dev', '-d', 'app',
                         '-Atc', "SELECT to_regclass('public.isolation_probe') IS NULL")
            assert absent.strip() == 't', absent
        finally:
            for process, log, log_path in active:
                process.terminate()
                try:
                    process.wait(timeout=30)
                finally:
                    log.close()
                output = log_path.read_text()
                match = re.search(r'Task project: (\S+)', output)
                if match:
                    assert not resources(match[1]), output
        print('PASS concurrent loopback servers, isolated PostgreSQL/Redis stacks and cancellation cleanup', flush=True)

        # An unrelated resource with a matching Compose project but no owner
        # label must survive explicit cleanup.
        project = f'{config["name"]}-agent-' + 'a' * 24
        volume = project + '-foreign'
        run('docker', 'volume', 'create', '--label', f'com.docker.compose.project={project}', volume)
        try:
            run(launcher, 'cleanup', project, cwd=repo, expected=1)
            run('docker', 'volume', 'inspect', volume)
        finally:
            run('docker', 'volume', 'rm', volume)
        print('PASS cleanup rejects resources without ownership labels', flush=True)


if __name__ == '__main__':
    main()
