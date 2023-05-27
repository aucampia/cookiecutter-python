
all:
.PHONY: all

python_version?=3.7
pip_compile=pipx run --spec=pip-tools --python=python$(python_version) pip-compile

requirement%.txt: requirement%.in
	$(pip_compile) \
		--verbose \
		--annotate \
		--generate-hashes \
		--resolver backtracking \
		--output-file $(@) \
		$(<)

all: requirements.txt
