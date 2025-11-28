echo "Initializing GraphRAG index..."
python -m graphrag init --force --root $1 2>&1

echo "Copying settings.yaml..."
cp settings.yaml $1/settings.yaml
sleep 5

echo "Configuring prompts..."
python -m graphrag prompt-tune --root $1 --config $2 --no-discover-entity-types --output $1/prompts --domain "code generation" 2>&1

echo "Populating GraphRAG index..."
python -m graphrag index --root $1 2>&1