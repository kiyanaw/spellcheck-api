FROM public.ecr.aws/lambda/python:3.12
RUN pip install hfst-altlab --root-user-action=ignore
COPY src/ ${LAMBDA_TASK_ROOT}/
CMD ["index.handler"]
