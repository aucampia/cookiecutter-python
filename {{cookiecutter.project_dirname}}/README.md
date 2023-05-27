# ...

```bash
poetry install
poetry run {{ cookiecutter.cli_name }}

{% if cookiecutter.build_tool == "go-task" %}
task help
task validate:fix validate
{% elif cookiecutter.build_tool == "gnu-make" %}
make help
make validate-fix validate
{% elif cookiecutter.build_tool == "poe" %}
poetry run poe help
poetry run poe validate-fix && poetry run poe validate
{% else %}
{{ None["[ERROR] Invalid build_tool " ~ cookiecutter.build_tool][0] }}
{% endif %}
```

## Using docker devtools

```bash
make -C devtools -B
docker compose build

{% if cookiecutter.build_tool == "go-task" %}
docker compose run --rm python-devtools task help
docker compose run --rm python-devtools task validate:fix validate
{% elif cookiecutter.build_tool == "gnu-make" %}
docker compose run --rm python-devtools make help
docker compose run --rm python-devtools make validate-fix validate
{% elif cookiecutter.build_tool == "poe" %}
docker compose run --rm python-devtools run poe help
docker compose run --rm python-devtools run poe validate-fix && poetry run poe validate
{% else %}
{{ None["[ERROR] Invalid build_tool " ~ cookiecutter.build_tool][0] }}
{% endif %}
```

## Updating from template base

```bash
pipx run --spec=cruft cruft update
```
