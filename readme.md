
## Running locally via Docker

1. Install [Docker](https://docs.docker.com/engine/install/) for your platform first, make sure you have [Docker Compose](https://docs.docker.com/compose/install/) as well
2. Clone this repository [gitlab.akvelon.net/sdc/summer-internship-ai-chat-platform/study-assistant](https://gitlab.akvelon.net/sdc/summer-internship-ai-chat-platform/study-assistant/-/tree/dev)
3. Create a file in the root of the repository named `.env` with the following content:
```
openai_key=sk-...
```
Replace `sk-...` with valid OpenAI API key

4. Run `docker-compose up` in the root of the repositoty.
5. You should see something like:
```log
Attaching to study-assistant-study-assistant-1
study-assistant-study-assistant-1  | INFO:     Started server process [1]
study-assistant-study-assistant-1  | INFO:     Waiting for application startup.
study-assistant-study-assistant-1  | INFO:     Application startup complete.
study-assistant-study-assistant-1  | INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

Now you should be able to acess API docs by visiting [http://localhost:8080/docs](http://localhost:8080/docs)

## Authors
- Artem Halushka
- Braxton Diaz
- Eugene Olonov
- Kirill Ustinov
- Lyubomyr Kryshtanovskyi

## License
MIT