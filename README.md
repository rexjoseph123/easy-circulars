# Easy Circulars

## Setup

### Intel environment
```bash
export https_proxy=http://proxy-dmz.intel.com:912
export http_proxy=http://proxy-dmz.intel.com:912
export HTTPS_PROXY=http://proxy-dmz.intel.com:912
export HTTP_PROXY=http://proxy-dmz.intel.com:912
```


### Mandatory services
```bash
export no_proxy=127.0.0.1,localhost,.intel.com,10.235.124.11,10.235.124.12,10.235.124.13,10.96.0.0/12,10.235.64.0/18,chatqna-xeon-ui-server,chatqna-xeon-backend-server,dataprep-redis-service,tei-embedding-service,retriever,tei-reranking-service,tgi-service,vllm_service,backend,mongodb,tei-reranking-server,tei-embedding-server,groq-service
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export LLM_MODEL_ID="meta-llama/Meta-Llama-3.1-8B-Instruct"
export INDEX_NAME="rag-redis"
export REDIS_URL="redis://redis-vector-db:6379"
export SERVER_HOST_URL=localhost:9001
export HUGGINGFACEHUB_API_TOKEN=<token>
export MEGA_SERVICE_PORT=9001
export EMBEDDING_SERVER_HOST_IP=localhost
export EMBEDDING_SERVER_PORT=6006
export RETRIEVER_SERVICE_HOST_IP=localhost
export RETRIEVER_SERVICE_PORT=5007
export RERANK_SERVER_HOST_IP=localhost
export RERANK_SERVER_PORT=8808
export LLM_SERVER_HOST_IP=localhost
export LLM_SERVER_PORT=5099
export GROQ_API_KEY=<GROQ_API_KEY>
export MONGO_HOST=localhost
export MONGO_PORT=27017
export MONGO_DB=easy_circulars
```
Run the compose file:
```bash
docker compose -f install/docker/docker-compose-dev.yaml up
```

---

### Ingesting Mock Data into MongoDB

#### Enter the MongoDB container
```bash
 docker exec -it mongodb mongosh
```

#### Switch to the `easy_circulars` database
```javascript
use easy_circulars
```

#### Insert mock circulars
```javascript
const mockCirculars = [ { _id: '1', title: "Master Circular – Deendayal Antyodaya Yojana - National Rural Livelihoods Mission (DAY-NRLM)", tags: ["master", "rural"], date: "2019-07-01", bookmark: false, url: "/pdfs/4MC01072019506189EF9A684645AF078EAA43E6BFC5.pdf", conversation_id: "", references: ['2', '3']}, { _id: '2', title: "Master Circular – Deendayal Antyodaya Yojana - National Rural Livelihoods Mission (DAY-NRLM)", tags: ["master", "rural"], date: "2018-07-03", bookmark: false, url: "/pdfs/09MC626B2B1F53BE4DD8B0A000EBAC40E2DB.pdf", conversation_id: "", references: []}, { _id: '3', title: "Priority Sector Lending- Restructuring of SGSY as National Rural Livelihood Mission (NRLM) - Aajeevika", tags: ["lending", "rural"], date: "2013-06-27", bookmark: false, url: "/pdfs/NRLM27062013.pdf", conversation_id: "", references: []}];

db.circulars.insertMany(mockCirculars);
```

#### Check if data has been inserted
```javascript
db.circulars.find().pretty();
```

#### Exit Mongo Shell
```javascript
exit
```

---

### Dataprep Service (New terminal - only required when uploading files/debugging)
#### Activate environment:
```bash
python3 -m venv venv
source venv/bin/activate
cd comps/
pip install -r requirements.txt # only once
cd dataprep/
pip install -r requirements.txt # only once

export PYTHONPATH=<path/to/easy-circulars/dir>
export HUGGINGFACEHUB_API_TOKEN=<token>
export REDIS_URL=redis://redis-vector-db:6379
export SERVER_HOST_IP=<your_server_host_ip>
export SERVER_PORT=<your_server_port>
export no_proxy=127.0.0.1,localhost,.intel.com,10.235.124.11,10.235.124.12,10.235.124.13,10.96.0.0/12,10.235.64.0/18,chatqna-xeon-ui-server,chatqna-xeon-backend-server,dataprep-redis-service,tei-embedding-service,retriever,tei-reranking-service,tgi-service,vllm_service,backend,mongodb,tei-reranking-server,tei-embedding-server,groq-service
```

#### Run the service:
```bash
python3 prepare_doc_redis.py
```
The dataprep service will be running on http://localhost:6007

#### Test the dataprep component by uploading a file:
```bash
curl -X POST "http://localhost:6007/v1/dataprep" -H "Content-Type: multipart/form-data" -F "files=@<path/to/pdf>"
```

---

### Retriever Service (New terminal - only required when changes are made/debugging)
#### Activate environment:
```bash
source venv/bin/activate
cd comps/retriever
pip install -r requirements.txt # only once

export PYTHONPATH=<path/to/ai-agents/dir>
export HUGGINGFACEHUB_API_TOKEN=<token>
export REDIS_URL=redis://redis-vector-db:6379
export INDEX_NAME="rag-redis"
export no_proxy=127.0.0.1,localhost,.intel.com,10.235.124.11,10.235.124.12,10.235.124.13,10.96.0.0/12,10.235.64.0/18,chatqna-xeon-ui-server,chatqna-xeon-backend-server,dataprep-redis-service,tei-embedding-service,retriever,tei-reranking-service,tgi-service,vllm_service,backend,mongodb,tei-reranking-server,tei-embedding-server,groq-service
```

#### Run the service:
```bash
python3 retriever_redis.py
```

#### Test the retriever component:
```bash
export your_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
curl http://localhost:7000/v1/retrieval \
  -X POST \
  -d "{\"text\":\"test\",\"embedding\":${your_embedding}}" \
  -H 'Content-Type: application/json'
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
export REDIS_URL="redis://redis-vector-db:6379"
export SERVER_HOST_URL=localhost:9001
export HUGGINGFACEHUB_API_TOKEN=<token>
export MEGA_SERVICE_PORT=9001
export EMBEDDING_SERVER_HOST_IP=localhost
export EMBEDDING_SERVER_PORT=6006
export RETRIEVER_SERVICE_HOST_IP=localhost
export RETRIEVER_SERVICE_PORT=5007
export RERANK_SERVER_HOST_IP=localhost
export RERANK_SERVER_PORT=8808
export LLM_SERVER_HOST_IP=localhost
export LLM_SERVER_PORT=5099
export GROQ_API_KEY=<GROQ_API_KEY>
export MONGO_HOST=localhost
export MONGO_PORT=27017
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
curl -X POST "http://localhost:9001/conversation/new" -d '{"db_name": "easy_circulars"}'  | jq  
```

#### Continue a conversation:
```bash
curl -X POST "http://localhost:9001/conversation/{conversation_id}" \
     -H "Content-Type: application/json" \
     -d '{"db_name": "easy_circulars", "question": "What is DAY-NRLM?"}' | jq
```

#### Get conversation history:
```bash
curl -X GET "http://localhost:9001/conversation/{conversation_id}?db_name=easy_circulars" | jq
```

#### Delete conversation:
```bash
curl -X DELETE "http://localhost:9001/conversation/{conversation_id}?db_name=easy_circulars" | jq
```

#### List all conversations:
```bash
curl -X GET "http://localhost:9001/conversations?limit=3&db_name=easy_circulars" | jq     
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

### Debugging:
#### Groq service:
```bash
curl -N -X POST http://localhost:5099/v1/chat/completions \
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
