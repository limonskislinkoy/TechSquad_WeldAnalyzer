FROM pytorch/pytorch:2.7.0-cuda12.6-cudnn9-runtime

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000 8001

COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]