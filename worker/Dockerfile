FROM python:3.13-slim-bookworm

# Install necessary system packages for building and running 'isolate'
RUN apt-get update && apt-get install -y \
    build-essential \
    libcap-dev \
    git \
    curl \
    pkg-config \
    libsystemd-dev \
    && apt-get install -y --no-install-recommends \
        linux-headers-$(dpkg --print-architecture) \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Clone, build, and install 'isolate'
ARG ISOLATE_VERSION=v2.2.1
WORKDIR /tmp
RUN git clone --depth 1 --branch ${ISOLATE_VERSION} https://github.com/ioi/isolate.git
WORKDIR /tmp/isolate
RUN make isolate && make install

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js for JavaScript support
ARG NODE_VERSION=20
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install OpenJDK for Java support
ARG JAVA_VERSION=17
RUN apt-get update && apt-get install -y openjdk-${JAVA_VERSION}-jdk-headless && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy entire worker code into the container
COPY . .

# Get environment variables to configure Redis connection
ENV REDIS_HOST=queue
ENV REDIS_PORT=6379
ENV REDIS_PREFIX=kodejudge

# Command to run the worker
CMD ["sh", "-c", "rq worker --url redis://$REDIS_HOST:$REDIS_PORT ${REDIS_PREFIX}_submission_queue"]
