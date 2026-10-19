FROM mcr.microsoft.com/devcontainers/python:3-3.12-bookworm

ARG TARGETARCH

RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        cmake \
        libcairo2-dev \
        pkg-config \
        python3-dev \
    && changie_version="1.26.0" \
    && case "${TARGETARCH}" in \
        amd64) changie_sha256="8586d01c321d3958bac72a7b3aeb29744b31bdabb06ffc65dbc4fb018a04f3d1" ;; \
        arm64) changie_sha256="d31e2b7570e479fdebf43737458173ee9bdc90e3cd3d5aece0bf15a43a71eb50" ;; \
        *) echo "Unsupported architecture: ${TARGETARCH}" >&2; exit 1 ;; \
    esac \
    && changie_deb="changie_${changie_version}_linux_${TARGETARCH}.deb" \
    && curl -fsSL \
        "https://github.com/miniscruff/changie/releases/download/v${changie_version}/${changie_deb}" \
        -o "/tmp/${changie_deb}" \
    && echo "${changie_sha256}  /tmp/${changie_deb}" | sha256sum -c - \
    && apt-get install -y "/tmp/${changie_deb}" \
    && rm -f "/tmp/${changie_deb}" \
    && rm -rf /var/lib/apt/lists/*
