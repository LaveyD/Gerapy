ARG PYTHON_IMAGE=python:3.10-slim
FROM ${PYTHON_IMAGE} AS build
ENV PATH="/root/.local/bin:$PATH"
WORKDIR /app
COPY pyproject.toml README.md LICENSE /app/
COPY poetry.lock /app/
COPY gerapy /app/gerapy
COPY backend /app/backend
# Install poetry
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends curl; \
    curl -sSL https://install.python-poetry.org | python3 -; \
    poetry --version
# Build gerapy
RUN set -eux; \
    poetry install; \
    poetry build --format wheel


FROM ${PYTHON_IMAGE}
# Install gerapy
ENV GERAPY_HOME_DIR=/home/gerapy \
    GERAPY_GROUP=gerapy \
    GERAPY_GID=10000 \
    GERAPY_USER=gerapy \
    GERAPY_UID=10000 \
    GERAPY_PORT=8000
WORKDIR $GERAPY_HOME_DIR
COPY --from=build /app/dist/gerapy-*.whl /tmp/
RUN \
    set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends tini gosu; \
    pip install /tmp/gerapy-*.whl psycopg2-binary; \
    rm -f /tmp/gerapy-*.whl; \
    mkdir -p $GERAPY_HOME_DIR; \
    addgroup --gid $GERAPY_GID $GERAPY_GROUP; \
    adduser --uid $GERAPY_UID --home $GERAPY_HOME_DIR --ingroup $GERAPY_GROUP $GERAPY_USER; \
    chown $GERAPY_USER:$GERAPY_GROUP $GERAPY_HOME_DIR; \
    pip cache purge; \
    apt autoclean; \
    rm -rf /var/lib/apt/lists/*;
# Build run script
RUN \
    set -eux; \
    runscript="/usr/local/bin/gerapy-runner"; \
    echo "#!/bin/sh -ex" > $runscript; \
    echo >> $runscript; \
    echo "find \"$GERAPY_HOME_DIR\" \! -user \"$GERAPY_USER\" -exec chown $GERAPY_USER:$GERAPY_GROUP '{}' +" >> $runscript; \
    cmd="gosu $GERAPY_USER:$GERAPY_GROUP gerapy"; \
    echo "$cmd init ." >> $runscript; \
    echo "$cmd migrate" >> $runscript; \
    echo "$cmd initadmin" >> $runscript; \
    echo "$cmd runserver 0.0.0.0:$GERAPY_PORT" >> $runscript; \
    chmod +x $runscript;
VOLUME $GERAPY_HOME_DIR
EXPOSE $GERAPY_PORT
ENTRYPOINT ["tini", "--"]
CMD ["gerapy-runner"]
