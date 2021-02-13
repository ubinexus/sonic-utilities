FROM docker-sonic-vs

ARG docker_container_name

ADD ["wheels", "/wheels"]

RUN pip3 install --force-reinstall /wheels/sonic-utilities-*.whl
