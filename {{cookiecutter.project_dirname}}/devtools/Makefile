
all:
.PHONY: all

pip_compile=uv pip compile

requirement%.txt: requirement%.in
	$(pip_compile) \
		--verbose \
		--annotate \
		--generate-hashes \
		--resolver backtracking \
		--output-file $(@) \
		$(<)

all: requirements.txt
