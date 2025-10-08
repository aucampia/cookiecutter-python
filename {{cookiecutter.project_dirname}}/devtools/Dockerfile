FROM docker.io/library/golang:1.25.2-alpine@sha256:6104e2bbe9f6a07a009159692fe0df1a97b77f5b7409ad804b17d6916c635ae5 AS golang

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

FROM docker.io/mikefarah/yq:4@sha256:76def1f56f456ecc1c3173ea275218ee17139bc2018c5a07887b15afd88ec03e AS yq

# ... {% if False %}
FROM ghcr.io/astral-sh/uv:bookworm@sha256:25c897bcd83092144443675c287fef6bdc92e5ee6f2774d8f5484075ba047039 AS python
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

