# Easy Circulars

## Intel environment
```bash
export https_proxy=http://proxy-dmz.intel.com:912
export http_proxy=http://proxy-dmz.intel.com:912
export HTTPS_PROXY=http://proxy-dmz.intel.com:912
export HTTP_PROXY=http://proxy-dmz.intel.com:912
```

## Mandatory services

### Export the following variables
```bash
export no_proxy=127.0.0.1,localhost,.intel.com,host.docker.internal,10.235.124.11,10.235.124.12,10.235.124.13,10.96.0.0/12,10.235.64.0/18,chatqna-xeon-ui-server,chatqna-xeon-backend-server,dataprep-redis-service,tei-embedding-service,retriever,tei-reranking-service,tgi-service,vllm_service,backend,mongodb,tei-reranking-server,tei-embedding-server,groq-service
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export LLM_MODEL_ID="meta-llama/Meta-Llama-3.1-8B-Instruct"
export INDEX_NAME="rag-redis"
export REDIS_URL="redis://easy-circulars-redis:6379"
export SERVER_HOST_URL=localhost:9001
export HUGGINGFACEHUB_API_TOKEN=<token>
export MEGA_SERVICE_PORT=9001
export EMBEDDING_SERVER_HOST_IP=localhost
export EMBEDDING_SERVER_PORT=6010
export RETRIEVER_SERVICE_HOST_IP=localhost
export RETRIEVER_SERVICE_PORT=5011
export RERANK_SERVER_HOST_IP=localhost
export RERANK_SERVER_PORT=8810
export LLM_SERVER_HOST_IP=localhost
export LLM_SERVER_PORT=5101
export GROQ_API_KEY=<GROQ_API_KEY>
export MONGO_HOST=localhost
export MONGO_PORT=27018
export MONGO_DB=easy_circulars
export PDF_DIR=<path/to/easy-circulars/ui/public/pdfs>
export SERVER_HOST_IP=host.docker.internal
export SERVER_PORT=9001     
export DATAPREP_HOST_IP=host.docker.internal
export DATAPREP_PORT=6007
export NEO4J_URI="bolt://easy-circulars-neo4j:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="password"
```

### Build the Webscraper, Groq and Retriever images:
```bash
docker buildx build --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -t easy-circulars/webscraper:latest -f comps/webscraper/Dockerfile .
docker buildx build --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -t easy-circulars/groq:latest -f comps/groq/Dockerfile  .;
docker buildx build --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -t easy-circulars/retriever:latest -f comps/retriever/Dockerfile . 
```

### Run the compose file:
```bash
docker compose -f install/docker/docker-compose-dev.yaml up
```

---

## Dataprep Service (New terminal - required by web scraper)
### Activate environment:
```bash
python3 -m venv venv
source venv/bin/activate
cd comps/
pip install -r requirements.txt # only once
cd dataprep/
pip install -r requirements.txt # only once

export PYTHONPATH=<path/to/easy-circulars/dir>
export HUGGINGFACEHUB_API_TOKEN=<token>
export REDIS_URL="redis://localhost:6381"
export LLM_SERVER_HOST_IP=localhost
export LLM_SERVER_PORT=5101
export no_proxy=127.0.0.1,localhost,.intel.com,10.235.124.11,10.235.124.12,10.235.124.13,10.96.0.0/12,10.235.64.0/18,chatqna-xeon-ui-server,chatqna-xeon-backend-server,dataprep-redis-service,tei-embedding-service,retriever,tei-reranking-service,tgi-service,vllm_service,backend,mongodb,tei-reranking-server,tei-embedding-server,groq-service
```

### Run the service:
```bash
python3 prepare_doc_redis.py
```
The dataprep service will be running on http://localhost:6007

### Test the dataprep component by uploading a file:
To use lightweight PDF parser:
```bash
curl -X POST "http://localhost:6007/v1/dataprep" -H "Content-Type: multipart/form-data" -F "files=@<path/to/pdf>" -F "parser_type=lightweight"
```
To use default PDF parser:
```bash
curl -X POST "http://localhost:6007/v1/dataprep" -H "Content-Type: multipart/form-data" -F "files=@<path/to/pdf>"
```

---

## Backend service (new terminal)
```bash
export PYTHONPATH=<path/to/easy-circulars/dir>
export no_proxy=127.0.0.1,localhost,.intel.com,10.235.124.11,10.235.124.12,10.235.124.13,10.96.0.0/12,10.235.64.0/18,chatqna-xeon-ui-server,chatqna-xeon-backend-server,dataprep-redis-service,tei-embedding-service,retriever,tei-reranking-service,tgi-service,vllm_service,backend,mongodb,tei-reranking-server,tei-embedding-server,groq-service
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export LLM_MODEL_ID="meta-llama/Meta-Llama-3.1-8B-Instruct"
export INDEX_NAME="rag-redis"
export REDIS_URL="redis://localhost:6381"
export SERVER_HOST_URL=localhost:9001
export HUGGINGFACEHUB_API_TOKEN=<token>
export MEGA_SERVICE_PORT=9001
export EMBEDDING_SERVER_HOST_IP=localhost
export EMBEDDING_SERVER_PORT=6010
export RETRIEVER_SERVICE_HOST_IP=localhost
export RETRIEVER_SERVICE_PORT=5011
export RERANK_SERVER_HOST_IP=localhost
export RERANK_SERVER_PORT=8810
export LLM_SERVER_HOST_IP=localhost
export LLM_SERVER_PORT=5101
export GROQ_API_KEY=<GROQ_API_KEY>
export MONGO_HOST=localhost
export MONGO_PORT=27018
export MONGO_DB=easy_circulars

# Activate the environment
source venv/bin/activate
cd comps/
```

### Run the service:
```bash
python3 main.py
```
The backend will be running on http://localhost:9001

### Test the backend
#### Start a new conversation:
```bash
curl -X POST "http://localhost:9001/api/conversations/new" -d '{"db_name": "easy_circulars"}'  | jq  
```

#### Continue a conversation:
```bash
curl -X POST "http://localhost:9001/api/conversations/{conversation_id}" \
     -H "Content-Type: application/json" \
     -d '{"db_name": "easy_circulars", "question": "What is DAY-NRLM?"}' | jq
```

#### Get conversation history:
```bash
curl -X GET "http://localhost:9001/api/conversations/{conversation_id}?db_name=easy_circulars" | jq
```

#### Delete conversation:
```bash
curl -X DELETE "http://localhost:9001/api/conversations/{conversation_id}?db_name=easy_circulars" | jq
```

#### List all conversations:
```bash
curl -X GET "http://localhost:9001/api/conversations?limit=3&db_name=easy_circulars" | jq     
```

---

## Extracting PDFs from the RBI Website using the Web Scraper Service

To extract circulars for a specific month and year, send a POST request to the service:
```bash
curl -X POST "http://localhost:5102/v1/scrape" \    
     -H "Content-Type: application/json" \
     -d '{"month": 11, "year": 2023}'
```

---

## UI (new terminal)
```bash
export no_proxy=127.0.0.1,localhost,.intel.com,10.235.124.11,10.235.124.12,10.235.124.13,10.96.0.0/12,10.235.64.0/18,chatqna-xeon-ui-server,chatqna-xeon-backend-server,dataprep-redis-service,tei-embedding-service,retriever,tei-reranking-service,tgi-service,vllm_service,backend,mongodb,tei-reranking-server,tei-embedding-server,groq-service
export SERVER_HOST_URL=localhost:9001
export NEXT_PUBLIC_SERVER_URL=localhost:9001

# Install dependencies
cd ui
npm install
```

### Start the UI:
```bash
npm run dev
```

The frontend will be running on http://localhost:3000

---

## Debugging:
### Groq service:
```bash
curl -N -X POST http://localhost:5101/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "What are the benefits of microservices?"
      }
    ],
    "stream": true
  }'
```
