ARG FAC_VER=stable-rootless

ARG PY_VER=3.14

# stage 1: python and packages
FROM --platform=$BUILDPLATFORM python:${PY_VER}-slim-trixie AS pyenv

ARG POETRY_HOME=/opt/poetry
ARG TARGETARCH
ARG PY_VER

RUN python3 -m venv $POETRY_HOME \
    && $POETRY_HOME/bin/pip install poetry==2.2

COPY . /root/server/

RUN cd /root/server \
    && $POETRY_HOME/bin/poetry install --no-root \
    && $POETRY_HOME/bin/poetry build \
    && if [ "$TARGETARCH" = "amd64" ]; then PIP_PLATFORM="manylinux2014_x86_64"; \
       elif [ "$TARGETARCH" = "arm64" ]; then PIP_PLATFORM="manylinux2014_aarch64"; \
       else echo "Unsupported target architecture: $TARGETARCH" && exit 1; fi \
    && $POETRY_HOME/bin/poetry run python -m pip wheel pyaes --wheel-dir /tmp/wheels \
    && $POETRY_HOME/bin/poetry run python -m pip install \
       --platform $PIP_PLATFORM \
       --target /root/site-packages \
       --only-binary=:all: \
       --find-links /tmp/wheels \
       dist/*.whl psutil

# stage 2: python dependencies (multi-arch)
FROM python:${PY_VER}-slim-trixie AS pydeps

ARG PY_VER
ARG EXPORT_PREFIX=/root/export_rootfs

RUN UNAME_M=$(uname -m) \
    && if [ "$UNAME_M" = "x86_64" ]; then ARCH_DIR="x86_64-linux-gnu"; \
    elif [ "$UNAME_M" = "aarch64" ]; then ARCH_DIR="aarch64-linux-gnu"; \
    else echo "Unsupported architecture: $UNAME_M" && exit 1; fi \
    && mkdir -p $EXPORT_PREFIX/usr/lib/$ARCH_DIR/ \
    && cp -a /usr/lib/$ARCH_DIR/libsqlite* $EXPORT_PREFIX/usr/lib/$ARCH_DIR/ \
    && cp -a /usr/local/ $EXPORT_PREFIX/usr/ \
    && rm -rf $EXPORT_PREFIX/usr/local/lib/python${PY_VER}/site-packages/

# stage 3: main image
FROM factoriotools/factorio:${FAC_VER}

ARG PY_VER

COPY --from=pydeps /root/export_rootfs/ /
COPY --from=pyenv /root/site-packages/ /usr/local/lib/python${PY_VER}/site-packages/

COPY docker-entrypoint.sh /

ENTRYPOINT ["/usr/local/bin/python3", "-m", "facmgr.server", "-E", "/docker-entrypoint.sh"]
