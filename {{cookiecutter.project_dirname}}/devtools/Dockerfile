FROM docker.io/library/golang:1.25.4-alpine@sha256:d3f0cf7723f3429e3f9ed846243970b20a2de7bae6a5b66fc5914e228d831bbb AS golang

RUN \
    go env > /usr/local/bin/goenv.sh && \
    true

COPY go.mod go.sum tools.go /var/tmp/build/

RUN \
    export GOBIN=/usr/local/bin && \
    cd /var/tmp/build/ && \
    awk -F '"' '/_.*toolchain/{print $2}' tools.go | xargs -t -I{} go install {} && \
    rm -rf "$(go env GOPATH)" && \
    rm -rf /var/tmp/build/* && \
    find "${GOBIN}" && \
    true

FROM docker.io/mikefarah/yq:4@sha256:224eec1bdaf4903221117d65dd95a0f4f4a6d4e46c88e2c81e09398d1f2753a1 AS yq

# ... {% if False %}
FROM ghcr.io/astral-sh/uv:bookworm@sha256:333a52dddc0b1b957b385201dd3baad65f68e63bbe1705879a9931e65bed25c6 AS python
# {% else %}{{"\n"}}FROM docker.io/library/python:{{ cookiecutter.python_version }} AS python{% endif %}
ENTRYPOINT [  ]

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN \
    apt-get update && \
    apt-get install -y \
        --no-install-recommends \
        make \
        socat \
        ca-certificates \
        curl \
        busybox \
        git \
        rsync \
        libarchive-tools \
        jq \
        yq \
        python-is-python3 \
        && \
    rm -vr /var/lib/apt/lists/* && \
    true

ENV UV_PYTHON_BIN_DIR=/usr/local/bin
ENV UV_PYTHON_INSTALL_DIR=/usr/local/share/uv/python
ENV UV_TOOL_BIN_DIR=/usr/local/bin
ENV UV_TOOL_DIR=/usr/local/share/uv/tools
ENV UV_LINK_MODE=copy

COPY requirements.txt /var/tmp/build/requirements.txt

COPY --from=yq /usr/bin/yq /usr/local/bin/
COPY --from=golang /usr/local/bin/goenv.sh /usr/local/bin/goenv.sh
COPY --from=golang /usr/local/bin/task /usr/local/bin/task
COPY --from=golang /usr/local/bin/yamlfmt /usr/local/bin/yamlfmt
COPY --from=golang /usr/local/bin/shfmt /usr/local/bin/shfmt

