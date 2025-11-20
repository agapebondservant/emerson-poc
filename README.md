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
  - Set up n8n
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

### 1.4 Set up custom ServingRuntime

### 1.5 Deploying IBM Granite 4 (ensure tool calling is enabled: https://www.ibm.com/granite/docs/run/granite-with-vllm-containerized)
Use the following settings as guidance:
```
export VLLM_ALLOW_LONG_MAX_MODEL_LEN=1
export VLLM_ALLOW_RUNTIME_LORA_UPDATING=True
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
python -m vllm.entrypoints.openai.api_server \
--model granite-4-tiny-version-1 \
--dtype=bfloat16 \
--max-model-len=8192 \
--trust-remote-code \
--gpu-memory-utilization=0.9 \
--tool-call-parser=hermes \
--enable-auto-tool-choice

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
### 1.7. Deploy n8n
```
source .env
sudo dnf install container-tools
oc new-project n8n
oc create secret docker-registry quay-creds --docker-server=quay.io --docker-username=${DOCKER_USERNAME}${DOCKER_USERNAME_SUFFIX} --docker-password=${DOCKER_PASSWORD} --docker-email=${DOCKER_EMAIL}
oc new-build --name=n8n-custom --to="quay.io/oawofolurh/n8n:latest" --strategy=docker --push-secret quay-creds --binary
oc start-build n8n-custom --from-dir docker --follow

# Run the following to install N8N:
oc new-project n8n
helm repo add community-charts https://community-charts.github.io/helm-charts
helm repo update
oc apply -f resources/n8n/pvc.yaml -n n8n
oc apply -f resources/n8n/deployment.yaml -n n8n
oc adm policy add-scc-to-user anyuid -z n8n-workflows
oc expose svc n8n-workflows -n n8n
# Access the N8N UI: echo http://`oc get route -o json | jq -r '.items[0].spec.host'`
```

### 1.8. Set up LanceDB MCP Server

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