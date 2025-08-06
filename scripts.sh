celery -A workers.celery_config worker -P eventlet -c 100 -l info -Q ingestion_queue -n ingestion_worker@%h
celery -A workers.celery_config worker -P eventlet -c 100 -l info -Q llm_queue -n llm_worker@%h
uvicorn app.main:app --reload
npm run dev
