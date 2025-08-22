# ...

```bash
## from GitHub
cookiecutter -v gh:aucampia/cookiecutter-python --overwrite-if-exists --output-dir var/baked/tmp
cruft create https://github.com/aucampia/cookiecutter-python

## from directory
uv tool install cookiecutter
cookiecutter -vvvv ~/sw/d/github.com/aucampia/cookiecutter-python --overwrite-if-exists --no-input --config-file tests/data/cookie-config/basic.yaml --output-dir var/baked/tmp
uv tool install cruft
cruft create ~/sw/d/github.com/aucampia/cookiecutter-python

## ...

\rm -rv var/baked/tmp

cookiecutter -vvvv ./ --overwrite-if-exists --no-input --config-file tests/data/cookie-config/basic.yaml --output-dir var/baked/tmp
cookiecutter -vvvv ./ --overwrite-if-exists --no-input --config-file tests/data/cookie-config/basic-make.yaml --output-dir var/baked/tmp

# WARNING: cruft works from HEAD so commit first
PYLOGGING_LEVEL=DEBUG cruft create ./ --overwrite-if-exists --no-input --config-file tests/data/cookie-config/basic.yaml --output-dir var/baked/tmp

(cd var/baked/tmp/example.project.basic && task configure)
(cd var/baked/tmp/example.project.basic && task validate:fix validate)
```

## Inspiration

- https://github.com/hackebrot/cookiecutter-examples/tree/master/create-directories
- https://github.com/audreyfeldroy/cookiecutter-pypackage
  - https://github.com/audreyfeldroy/cookiecutter-pypackage/blob/master/cookiecutter.json
- https://github.com/timhughes/cookiecutter-poetry
  - https://github.com/timhughes/cookiecutter-poetry/blob/master/cookiecutter.json
- https://github.com/johanvergeer/cookiecutter-poetry
  - https://github.com/johanvergeer/cookiecutter-poetry/blob/develop/cookiecutter.json
- https://github.com/cjolowicz/cookiecutter-hypermodern-python
  -  https://github.com/cjolowicz/cookiecutter-hypermodern-python/blob/main/cookiecutter.json

## devtools

```bash
docker compose build
docker compose run --rm devtools task help
docker compose run --rm devtools task configure validate
```

## updating


```bash
pipx upgrade-all
uv tool upgrade --all
poetry up --latest

# pipx run -q --spec=yq tomlq -r '.tool.poetry.dependencies | keys | .[] | select(. != "python") | (. + "@latest")' pyproject.toml | xargs -n1 echo poetry add
uv tool run -q --from=yq tomlq -r '.tool.poetry.dependencies | keys | .[] | select(. != "python") | (. + "@latest")' pyproject.toml | xargs -n1 echo poetry add

# pipx run -q --spec=yq tomlq -c '.tool.poetry.group | to_entries | .[] | [ "--group=" + .key, ((.value.dependencies | keys)[] | . + "@latest") ]' pyproject.toml | tr '\n' '\000' | xargs -0 -n1 bash -c 'echo "${1}" | jq -r ".[]" | xargs echo poetry add' --
uv tool run -q --from=yq tomlq -c '.tool.poetry.group | to_entries | .[] | [ "--group=" + .key, ((.value.dependencies | keys)[] | . + "@latest") ]' pyproject.toml | tr '\n' '\000' | xargs -0 -n1 bash -c 'echo "${1}" | jq -r ".[]" | xargs echo poetry add' --

code . --diff Taskfile.yml link_project/Taskfile.yml
code . --diff pyproject.toml link_project/pyproject.toml
code . --diff link_project/pkg_files/basic/cli/__init__.py link_project/pkg_files/minimal_typer/cli/__init__.py
code . --diff link_project/pkg_files/basic/cli/sub.py link_project/pkg_files/minimal_typer/cli/sub.py
```

## monkey sync

```bash
## Diff summary ...
diff -u -r -q \
    --exclude={.git,TEMPLATE-*.md,poetry.lock,__pycache__,*.egg-info,.pytest_cache,.mypy_cache,.venv,.tox,setup.py,.cache-*,dist,.coverage,coverage.xml,extra,LICENSE} \
    ~/sw/d/github.com/aucampia/cookiecutter-python/var/baked/tmp/example.project.basic/ ./

## vimdiff
diff -u -r \
    --exclude={.git,TEMPLATE-*.md,poetry.lock,__pycache__,*.egg-info,.pytest_cache,.mypy_cache,.venv,.tox,setup.py,.cache-*,dist,.coverage,coverage.xml,extra,LICENSE} \
    ~/sw/d/github.com/aucampia/cookiecutter-python/var/baked/tmp/example.project.basic/ ./ \
    | sed -E -n 's,^diff.* /,vimdiff /,gp'

## diff
diff -u -r \
    --exclude={.git,TEMPLATE-*.md,poetry.lock,__pycache__,*.egg-info,.pytest_cache,.mypy_cache,.venv,.tox,setup.py,.cache-*,dist,.coverage,coverage.xml,extra,LICENSE} \
    ~/sw/d/github.com/aucampia/cookiecutter-python/var/baked/tmp/example.project.basic/ ./
```

## ...

```bash
TEST_RAPID=true task test
TEST_RAPID=true task test -- -rA 'tests/test_bake.py::test_baked_cmd' --log-cli-level INFO
```

<!--
MARK 000
-->


## syncdown

```bash
vimdiff ./Taskfile.yml ./link_project/Taskfile.yml
```

```bash
pipx run --spec=cruft cruft update
```


```bash
GITHUB_REPOSITORY="$(gh repo view --json owner,name -q '.owner.login + "/" + .name')"
export DOCKER_BUILDKIT_CACHE_TO="type=registry,ref=ghcr.io/${GITHUB_REPOSITORY}:cache,mode=max"
export DOCKER_BUILDKIT_CACHE_FROM="type=registry,ref=ghcr.io/${GITHUB_REPOSITORY}:cache"

docker compose run --build --rm devtools task configure validate:static
```
