FROM python:3.10
COPY . /app
WORKDIR /app
RUN apt update -y && \
apt install -y curl git && \
rm -rf /var/lib/apt/lists/*
# Install pyenv to manage python versions

RUN git clone https://github.com/pyenv/pyenv.git /root/.pyenv

ENV PYENV_ROOT=/root/.pyenv
ENV PATH=$PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH
RUN pip install -r requirements.txt
ENTRYPOINT ["/bin/bash", "entrypoint.sh"]