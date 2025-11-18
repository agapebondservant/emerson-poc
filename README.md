# Code Translation with ColdFusion / CFML
## 1. Demonstration with continue.dev
### Running the ColdFusion app

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

## 2. Deploying IBM Granite 4
```
export VLLM_ALLOW_LONG_MAX_MODEL_LEN=1
export VLLM_ALLOW_RUNTIME_LORA_UPDATING=True
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
python -m vllm.entrypoints.openai.api_server \
--model granite-4-tiny-version-1 \
--port 8000 \
--dtype=bfloat16 \
--max-model-len=128000 \
--trust-remote-code \
--gpu-memory-utilization=0.9 \
--tool-call-parser=hermes \
--enable-auto-tool-choice

```

## 3. Setting up Minio for Object Storage
```
oc new-project minio --display-name="Minio S3 for LLMs"
oc apply -f resources/minio-all.yaml
export AWS_S3_ENDPOINT=https://`oc get route minio-api -ojson | jq -r ".spec.host"`
export AWS_ACCESS_KEY_ID=`oc get secret minio-secret -ojson | jq -r ".data.minio_root_user" | base64 --decode`
export AWS_SECRET_ACCESS_KEY=`oc get secret minio-secret -ojson | jq -r ".data.minio_root_password" | base64 --decode`
mc alias set cfdemo $AWS_S3_ENDPOINT $AWS_ACCESS_KEY_ID $AWS_SECRET_ACCESS_KEY
mc mb cfdemo/lancedb
mc anonymous set public cfdemo/lancedb
echo AWS_S3_ENDPOINT=$AWS_S3_ENDPOINT >> .env
echo AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID >> .env
echo AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY >> .env
```

## 4. Deploying Postgres Datagase
```
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
#brew install postgresql #for mac users
oc new-project postgresql
helm install my-postgresql bitnami/postgresql \
      --set postgresqlDatabase=demo \
      --set primary.persistence.size=10Gi
```

Test the installation:
```
export POSTGRES_PASSWORD=$(oc get secret my-postgresql -o jsonpath="{.data.postgres-password}" | base64 -d)
oc port-forward --namespace postgresql svc/my-postgresql 5432:5432
PGPASSWORD="$POSTGRES_PASSWORD" psql --host 127.0.0.1 -U postgres -d \
postgres -p 5432 -c "CREATE DATABASE demo;"
PGPASSWORD="$POSTGRES_PASSWORD" psql --host 127.0.0.1 -U postgres -d demo \
-p 5432 -f apps/demo.sql
```

To uninstall:
```
helm install my-postgresql
oc delete pvc data-my-postgresql-0 -npostgresql
```