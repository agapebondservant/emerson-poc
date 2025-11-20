cp settings.yaml $1/settings.yaml
python -m graphrag init --root $1 &2>1
python -m graphrag prompt-tune --root $1 --config $2 --no-discover-entity-types --domain "code generation" 2>&1
python -m graphrag index --method fast --root $1 2>&1