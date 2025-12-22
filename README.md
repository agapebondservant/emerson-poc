# Code Translation with ColdFusion / CFML

Contents
---
- Prepare environment variables
- Set up 
  - Pre-requisites
  - Deploy Dev Spaces
  - Set up continue.dev
  - Set up custom workbenches
  - Set up custom ServingRuntime
  - Deploy Granite 4 Tiny with Tool Calling
  - Set up Minio for Object Storage (for **LanceDB with GraphRAG**, **Kubeflow Pipeline Server**)
  - Set up Kubeflow Pipelines
  - Set up LanceDB MCP Server
  - Set up Llama Stack
- Synthetic Data Generation with sdg_hub
- GraphRAG with LanceDB
- Demonstration
  - Demonstration with Kubeflow Pipelines
  - Demonstration with Llama Stack Playground
  - Demonstration with continue.dev
  - Demonstration with n8n
  - Demonstration with multi-agentic app
- How-Tos

## 0. PREPARE ENVIRONMENT VARIABLES
Update .env.template as appropriate and rename to .env, then run
```
source .env
```

## 1. SET UP

### 1.0 Required software / Tested with

- Red Hat OpenShift 4.18+
- Red Hat OpenShift AI 2.22+
- 4X NVIDIA L40 GPUs
- 8+ vCPUs / 24+ GiB RAM
- OpenShift CLI (`oc`)
- Helm CLI (`helm`)

### 1.1 Deploy Dev Spaces(use <a href="https://github.com/settings/applications/new" target="_blank">DevSpaces documentation</a>)
Run the following script:
```
source .env
export DEVSPACES_CLIENT_ID=$DEVSPACES_CLIENT_ID
export DEVSPACES_CLIENT_SECRET=$DEVSPACES_CLIENT_SECRET
oc create namespace openshift-devspaces
envsubst < resources/templates/devspacessecret.yaml.in > resources/devspaces/secret.yaml
oc apply -f resources/devspaces/secret.yaml
```
Then install Dev Spaces: https://docs.redhat.com/en/documentation/red_hat_openshift_dev_spaces/3.24

### 1.2. Set up continue.dev

### 1.3 Set up custom workbenches
The following workbenches were used:
- Custom Agentic Workbench (CrewAI): <a href="https://quay.io/repository/oawofolurh/crewai-wb" target="_blank">Workbench Image</a>
- Custom GraphRAG Workbench: <a href="https://quay.io/repository/oawofolurh/graphrag-wb" target="_blank">Workbench Image</a>

Use the generated wb-secret.yaml file below to set up the 
Environment variables for the workbenches (under "Environment Variables" 
section, select Variable Type -> Upload, then upload the generated file below):
```
oc delete secret data-prep-wb --ignore-not-found
oc create secret generic data-prep-wb --from-env-file .env
oc get secret data-prep-wb -oyaml > wb-secret.yaml
```

### 1.4 Set up custom ServingRuntime
```
oc apply -f resources/vllm-serving-runtime/custom-vllm.yaml
```

### 1.5 Deploying IBM Granite 4 (ensure tool calling is enabled: https://www.ibm.com/granite/docs/run/granite-with-vllm-containerized)
Use the following settings as guidance:
```
# Granite 4 Tiny with Tool Calling
export VLLM_ALLOW_LONG_MAX_MODEL_LEN=1
python -m vllm.entrypoints.openai.api_server \
--model=granite-4-tiny-version-1 \
--dtype=bfloat16 \
--max-model-len=128000 \
--trust-remote-code \
--gpu-memory-utilization=0.9 \
--tool-call-parser=hermes \
--enable-auto-tool-choice

# intfloat/e5-mistral-7b-instruct for GraphRAG embedding
python -m vllm.entrypoints.openai.api_server \
--model=intfloat/e5-mistral-7b-instruct \
--task=embed
```

### 1.6. Deploying gpt-oss (or accessing via third party provider)
NOTE: <a href="https://openrouter.ai/" target="_blank>OpenRouter</a> was used for this project.

### 1.7. Set up Minio for Object Storage
```
oc new-project minio --display-name="Minio S3 for LLMs"
oc apply -f resources/minio-all.yaml
export AWS_S3_ENDPOINT=https://`oc get route minio-api -ojson | jq -r ".spec.host"`
export AWS_ACCESS_KEY_ID=`oc get secret minio-secret -ojson | jq -r ".data.minio_root_user" | base64 --decode`
export AWS_SECRET_ACCESS_KEY=`oc get secret minio-secret -ojson | jq -r ".data.minio_root_password" | base64 --decode`
mc alias set cfdemo $AWS_S3_ENDPOINT $AWS_ACCESS_KEY_ID $AWS_SECRET_ACCESS_KEY
mc mb cfdemo/data
mc anonymous set public cfdemo/data
echo AWS_S3_ENDPOINT=$AWS_S3_ENDPOINT >> .env
echo AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID >> .env
echo AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY >> .env
```
### 1.7. Deploy Kubeflow Pipelines
```
source .env
podman login -u ${DOCKER_USERNAME}${DOCKER_USERNAME_SUFFIX} -p ${DOCKER_PASSWORD} ${DOCKER_HOST}
podman pull quay.io/oawofolurh/graphrag-wb:latest
podman pull quay.io/oawofolurh/agentic-wb:latest
podman login -u $(oc whoami) -p $(oc whoami -t) image-registry.openshift-image-registry.svc:5000
podman tag quay.io/oawofolurh/graphrag-wb:latest image-registry.openshift-image-registry.svc:5000/oawofolurh/graphrag-wb:latest
podman tag quay.io/oawofolurh/graphrag-wb:latest image-registry.openshift-image-registry.svc:5000/oawofolurh/agentic-wb:latest
podman push image-registry.openshift-image-registry.svc:5000/oawofolurh/graphrag-wb:latest
podman push image-registry.openshift-image-registry.svc:5000/oawofolurh/agentic-wb:latest
python -m venv venv
source venv/bin/activate
pip install kfp==1.8.21 pyyaml==5.3.1 dotenv==0.9.9
python3 pipelines/kfp_pipeline.py
```

### 1.8. Set up LanceDB MCP Server
```
set -a
source .env
set +a
envsubst < templates/settings.yaml.in > notebooks/settings.yaml
```

### 1.9. Set up Llama Stack

## 2. Synthetic Data Generation with sdg_hub
See Jupyter Notebook: [notebooks/data_generator_rag_sdghub.ipynb](sdghub)

## 3. GraphRAG with LanceDB
See Jupyter Notebook: [notebooks/data_evaluator_graphrag.ipynb](graphrag)

## 4. Demonstration
### 4.1 Demonstration with Llama Stack Playground

### 4.2. Demonstration with continue.dev
##### Running the ColdFusion app

Shopping cart:
```
cd apps/shopping-cart
podman run -d -p 8080:8080 -p 8443:8443 -v $(pwd):/app --name shopping-cart ortussolutions/commandbox
```

Checkmate:
```
cd apps/Checkmate-CMS
podman run -d -p 8080:8080 -p 8443:8443 -v $(pwd):/app --name checkmate ortussolutions/commandbox
```

cf_golfap: (https://github.com/holtonma/cf_golfap.git)
```
cd apps/cf_golfap
podman run -d -p 8080:8080 -p 8443:8443 -v $(pwd):/app --name cf_golfap ortussolutions/commandbox
```

### 4.3. Demonstration with n8n

### 4.4. Demonstration with multi-agentic app
To run the app locally:
  1. Set up a virtual environment: python3.12 -m venv venv 
  2. Activate the virtual environment: source venv/bin/activate
  3. cd to the app directory: cd apps/code-translator
  4. Update .env.template as appropriate and rename to .env
  5. Install dependencies: pip install -r requirements.txt 
  6. Start the app: python3 -m streamlit run app.py

### 4.5. Demonstration with Kubeflow Pipelines

## 5. How-Tos (can convert to MCP servers)

### Get Size of LanceDB index
Run the following:
```
mc du cfdemo/data
```

### Generate Text Dump of git repository
Run the following:
```
gitingest <gitrepo> --include-pattern "**/*.cfm,**/*.cfc,**/*.cfml,**/*.java"
```
