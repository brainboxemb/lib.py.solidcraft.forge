ARG PYTHON_IMAGE
FROM ${PYTHON_IMAGE}

ARG SOLIDCRAFT_VERSION
ARG CADCRAFT_VERSION
ARG CADCRAFT_SHA256
ARG PYTHONSCAD_VERSION
ARG PYBOSL2_COMMIT
ARG CADQUERY_VERSION
ARG BUILD123D_VERSION
ARG PILLOW_SPEC
ARG TRIMESH_SPEC
ARG SCIPY_SPEC

LABEL org.opencontainers.image.source="https://github.com/brainboxemb/lib.py.solidcraft.forge"

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SOLIDCRAFT_GPU=cpu \
    BUILD123D_PYTHON=/opt/build123d/bin/python \
    PATH=/opt/solidcraft/bin:/opt/cadcraft/bin:$PATH

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
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

RUN set -eux; \
    archive="cadcraft-${CADCRAFT_VERSION}-linux-x86_64.tar.gz"; \
    url="https://github.com/storytold/cadcraft/releases/download/v${CADCRAFT_VERSION}/${archive}"; \
    mkdir -p /opt/cadcraft/bin /tmp/cadcraft; \
    curl --proto '=https' -fsSL "${url}" -o "/tmp/cadcraft/${archive}"; \
    echo "${CADCRAFT_SHA256}  /tmp/cadcraft/${archive}" | sha256sum -c -; \
    tar -xzf "/tmp/cadcraft/${archive}" \
        --strip-components=2 \
        -C /opt/cadcraft/bin \
        "cadcraft-${CADCRAFT_VERSION}-linux-x86_64/bin/cadcraft-cli"; \
    test -x /opt/cadcraft/bin/cadcraft-cli; \
    rm -rf /tmp/cadcraft

RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install \
        "Pillow${PILLOW_SPEC}" \
        "pythonscad==${PYTHONSCAD_VERSION}" \
        "git+https://github.com/pinkfish/pybosl2@${PYBOSL2_COMMIT}" \
        "cadquery==${CADQUERY_VERSION}" \
        "trimesh${TRIMESH_SPEC}" \
        "scipy${SCIPY_SPEC}" \
    && python -m venv /opt/build123d \
    && /opt/build123d/bin/python -m pip install --upgrade pip setuptools wheel \
    && /opt/build123d/bin/python -m pip install "build123d==${BUILD123D_VERSION}"

RUN solidcraft-cli --version \
    && cadcraft-cli --version \
    && python -c "import PIL, cadquery, scipy, trimesh" \
    && /opt/build123d/bin/python -c "import build123d"

WORKDIR /workspace
