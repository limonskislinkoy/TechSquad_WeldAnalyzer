#CUDA 12.8
#FROM pytorch/pytorch:2.7.0-cuda12.8-cudnn9-runtime
#CUDA 12.6
FROM pytorch/pytorch:2.7.0-cuda12.6-cudnn9-runtime
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir -p /app/data

WORKDIR /app

COPY reqierements.txt .

RUN pip install --no-cache-dir -r reqierements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
