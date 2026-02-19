FROM docker.io/library/golang:1.26.0-alpine@sha256:d4c4845f5d60c6a974c6000ce58ae079328d03ab7f721a0734277e69905473e5 AS golang

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

FROM docker.io/mikefarah/yq:4@sha256:a4c2cafdf4674b2dc3c6ac457fe1486d55d7d93edb3ed4459637afda3c286af6 AS yq

# ... {% if False %}
FROM ghcr.io/astral-sh/uv:bookworm@sha256:795e35a25bfa841d09f9367a1e938ed2b9d0e8a69ed275a75a396bd03c034517 AS python
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

