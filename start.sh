#!/bin/bash

cd server
uvicorn main:app --host 0.0.0.0 --port 8001 &
cd ../web
uvicorn main:app --host 0.0.0.0 --port 8000 &
wait
