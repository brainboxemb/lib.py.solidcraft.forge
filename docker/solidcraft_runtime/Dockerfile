ARG PYTHON_IMAGE
FROM ${PYTHON_IMAGE}

ARG SOLIDCRAFT_VERSION
ARG CAD_VERIFICATION_VERSION
ARG CAD_VERIFICATION_COMMIT

LABEL org.opencontainers.image.source="https://github.com/brainboxemb/lib.py.solidcraft.forge"

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SOLIDCRAFT_GPU=cpu \
    PATH=/opt/solidcraft/bin:$PATH

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        libdbus-1-3 \
        libegl1 \
        libfontconfig1 \
        libglib2.0-0 \
        libgl1 \
        libice6 \
        libsm6 \
        libx11-6 \
        libx11-xcb1 \
        libxcb-cursor0 \
        libxcb-xinerama0 \
        libxcb1 \
        libxext6 \
        libxi6 \
        libxkbcommon-x11-0 \
        libxkbcommon0 \
        libxrender1 \
    && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    archive="solidcraft-${SOLIDCRAFT_VERSION}-linux-x86_64.tar.gz"; \
    base="https://github.com/tangency-labs/solidcraft/releases/download/v${SOLIDCRAFT_VERSION}"; \
    mkdir -p /opt/solidcraft /tmp/solidcraft; \
    cd /tmp/solidcraft; \
    curl --proto '=https' -fsSLO "${base}/SHA256SUMS.txt"; \
    curl --proto '=https' -fsSLO "${base}/${archive}"; \
    grep "  ${archive}$" SHA256SUMS.txt | sha256sum -c -; \
    tar -xzf "${archive}" --strip-components=1 -C /opt/solidcraft; \
    test -x /opt/solidcraft/bin/solidcraft-cli; \
    rm -rf /tmp/solidcraft

RUN python -m pip install --upgrade pip setuptools \
    && python -m pip install \
        "PyYAML==6.0.3" \
        "https://github.com/brainboxemb/lib.py.cad.verfication/archive/${CAD_VERIFICATION_COMMIT}.zip"

RUN solidcraft-cli --version \
    && python -c "import importlib.metadata as m, cad_verification, yaml; actual=m.version('brainboxemb-cad-verification-lib'); expected='${CAD_VERIFICATION_VERSION}'; assert actual == expected, f'cad-verification {actual} != {expected}'"

WORKDIR /workspace
