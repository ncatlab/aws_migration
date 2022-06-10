FROM public.ecr.aws/lambda/python:3.9

COPY texlive.profile .

RUN yum install -y wget tar gzip perl perl-Digest-MD5 poppler-utils \
  && wget http://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz \
  && tar -xvzf install-tl-unx.tar.gz \
  && cd install-tl-* \
  && ./install-tl --profile=../texlive.profile \
  && echo "openin_any = p" >> /usr/local/texlive/texdir/texmf.cnf # For greater security

ENV PATH=/usr/local/texlive/texdir/bin/x86_64-linux:$PATH

RUN tlmgr install standalone xpatch tikz-cd xypic

COPY create_diagram.py ${LAMBDA_TASK_ROOT}
COPY tikz_diagram_template ${LAMBDA_TASK_ROOT}
COPY xypic_diagram_template ${LAMBDA_TASK_ROOT}

CMD [ "create_diagram.lambda_handler" ]
