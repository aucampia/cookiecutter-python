FROM docker.io/library/golang:1.25.2-alpine@sha256:06cdd34bd531b810650e47762c01e025eb9b1c7eadd191553b91c9f2d549fae8 AS golang

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

FROM docker.io/mikefarah/yq:4@sha256:75b3a60dce1fa4641b0f02bdb4465eddc5da95e62028118a292239ca8e3921e5 AS yq

# ... {% if False %}
FROM ghcr.io/astral-sh/uv:bookworm@sha256:317070e0bf9e1ab9aaabba2ef888b7d86179e9e9e29e4394dfbdeae1aad79080 AS python
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

RUN uv python install python3 python3.13

COPY requirements.txt /var/tmp/build/requirements.txt
RUN uv tool install \
    --constraints /var/tmp/build/requirements.txt \
    --python=3.13 \
    --with='poetry-plugin-up' poetry

COPY --from=yq /usr/bin/yq /usr/local/bin/
COPY --from=golang /usr/local/bin/goenv.sh /usr/local/bin/goenv.sh
COPY --from=golang /usr/local/bin/task /usr/local/bin/task
COPY --from=golang /usr/local/bin/yamlfmt /usr/local/bin/yamlfmt
COPY --from=golang /usr/local/bin/shfmt /usr/local/bin/shfmt

