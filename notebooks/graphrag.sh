echo "Copying settings.yaml..."
# cp settings.yaml $1/settings.yaml 2>&1

echo "Initializing GraphRAG index..."
# python -m graphrag init --root $1 2>&1

echo "Configuring prompts..."
python -m graphrag prompt-tune --root $1 --config $2 --no-discover-entity-types --domain "code generation" 2>&1

echo "Populating GraphRAG index..."
python -m graphrag index --method fast --root $1 2>&1