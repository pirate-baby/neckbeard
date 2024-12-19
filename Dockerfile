FROM python:3.10
COPY . /app
WORKDIR /app
RUN apt update -y && \
apt install -y curl git npm && \
rm -rf /var/lib/apt/lists/*
# Install pyenv to manage python versions

RUN git clone https://github.com/pyenv/pyenv.git /root/.pyenv
ENV NODE_OPTIONS=--max_old_space_size=10240
RUN npm install -g jscpd

ENV PYENV_ROOT=/root/.pyenv
ENV PATH=$PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH
RUN pip install -r requirements.txt
ENTRYPOINT ["/bin/bash", "entrypoint.sh"]