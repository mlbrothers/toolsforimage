These are the 3 commands for docker in sequence in order to push the docker image:
1. docker build -t toolsforimage .
2. docker tag toolsforimage mlbrothers2024/toolsforimage:latest
3. docker push mlbrothers2024/toolsforimage:latest

After these 3 commands, redeploy on railway