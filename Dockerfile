ARG FAC_VER=stable-rootless

# stage 1: python and packages
FROM python:3.13-slim-trixie AS pyenv

ARG POETRY_HOME=/opt/poetry EXPORT_PREFIX=/root/export_rootfs

RUN python3 -m venv $POETRY_HOME \
    && $POETRY_HOME/bin/pip install poetry==2.2

COPY . /root/server/

RUN cd /root/server \
    && $POETRY_HOME/bin/poetry install --no-root \
    && $POETRY_HOME/bin/poetry build \
    && $POETRY_HOME/bin/poetry run python -m pip install dist/*.whl psutil

RUN UNAME_M=$(uname -m) \
    && if [ "$UNAME_M" = "x86_64" ]; then ARCH_DIR="x86_64-linux-gnu"; \
    elif [ "$UNAME_M" = "aarch64" ]; then ARCH_DIR="aarch64-linux-gnu"; \
    else echo "Unsupported architecture: $UNAME_M" && exit 1; fi \
    && mkdir -p $EXPORT_PREFIX/usr/lib/$ARCH_DIR/ \
    && cp -a /usr/lib/$ARCH_DIR/libsqlite* $EXPORT_PREFIX/usr/lib/$ARCH_DIR/ \
    && cp -a /usr/local/ $EXPORT_PREFIX/usr/ \
    && rm -rf $EXPORT_PREFIX/usr/local/lib/python3.13/site-packages/ \
    && cp -a /root/.cache/pypoetry/virtualenvs/*/lib/python3.13/site-packages/ $EXPORT_PREFIX/usr/local/lib/python3.13/site-packages/


# stage 2: main image
FROM factoriotools/factorio:${FAC_VER}

COPY --from=pyenv /root/export_rootfs/ /

COPY docker-entrypoint.sh /

ENTRYPOINT ["/usr/local/bin/python3", "-m", "facmgr.server", "-E", "/docker-entrypoint.sh"]
