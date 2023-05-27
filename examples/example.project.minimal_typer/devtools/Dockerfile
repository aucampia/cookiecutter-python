FROM golang:1.19-bullseye AS golang

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

FROM docker.io/mikefarah/yq:4 as yq

# ... 
FROM docker.io/library/python:3.7 AS python


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
        && \
    rm -vr /var/lib/apt/lists/* && \
    true

COPY requirements.txt /var/tmp/build/requirements.txt
RUN python3 -m pip install \
        --no-cache-dir \
        --require-hashes  \
        --verbose \
        --use-pep517 \
        --requirement /var/tmp/build/requirements.txt && \
    rm -rf /var/tmp/build/requirements.txt && \
    true

COPY --from=yq /usr/bin/yq /usr/local/bin/
COPY --from=golang /usr/local/bin/goenv.sh /usr/local/bin/goenv.sh
COPY --from=golang /usr/local/bin/task /usr/local/bin/task


