FROM docker-sonic-vs

ARG docker_container_name

ADD ["wheels", "/wheels"]

RUN pip3 install --force-reinstall /wheels/sonic-utilities-1.2-py3-none-any.whl
