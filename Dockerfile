ARG FAC_VER=stable

# stage 1: python and packages
FROM python:3.13-slim-bookworm AS pyenv

ARG POETRY_HOME=/opt/poetry EXPORT_PREFIX=/root/export_rootfs

RUN apt-get -q update \
    && DEBIAN_FRONTEND=noninteractive apt-get -qy install build-essential \
    && python3 -m venv $POETRY_HOME \
    && $POETRY_HOME/bin/pip install poetry==1.8.4

COPY . /root/server/

RUN cd /root/server \
    && $POETRY_HOME/bin/poetry install --no-root \
    && $POETRY_HOME/bin/poetry build \
    && $POETRY_HOME/bin/poetry run python -m pip install dist/*.whl psutil

RUN mkdir $EXPORT_PREFIX/usr/lib/aarch64-linux-gnu/ -p \
    && cp -a /usr/lib/aarch64-linux-gnu/libsqlite* $EXPORT_PREFIX/usr/lib/aarch64-linux-gnu/ \
    && cp -a /usr/local/ $EXPORT_PREFIX/usr/ \
    && rm -rf $EXPORT_PREFIX/usr/local/lib/python3.13/site-packages/ \
    && cp -a /root/.cache/pypoetry/virtualenvs/*/lib/python3.13/site-packages/ $EXPORT_PREFIX/usr/local/lib/python3.13/site-packages/


# stage 2: main image
FROM factoriotools/factorio:${FAC_VER}

COPY --from=pyenv /root/export_rootfs/ /

COPY docker-entrypoint.sh /

ENTRYPOINT ["/usr/local/bin/python3", "-m", "facmgr.server", "-E", "/docker-entrypoint.sh"]
