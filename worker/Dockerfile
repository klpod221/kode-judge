FROM python:3.13-slim-bookworm

# Install necessary system packages for building and running 'isolate'
RUN apt-get update && apt-get install -y \
    build-essential \
    libcap-dev \
    git \
    curl \
    wget \
    pkg-config \
    libsystemd-dev \
    dirmngr \
    gnupg \
    ca-certificates \
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

# Install PHP runtime
ARG PHP_VERSION=8.2
RUN apt-get update && apt-get install -y \
    php${PHP_VERSION}-cli \
    php${PHP_VERSION}-mbstring \
    php${PHP_VERSION}-xml \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Lua interpreter
ARG LUA_VERSION=5.4
RUN apt-get update && apt-get install -y lua${LUA_VERSION} && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Free Pascal Compiler (supports multiple .pas files)
RUN apt-get update && apt-get install -y fp-compiler && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install SQLite3 for SQL support
RUN apt-get update && apt-get install -y sqlite3 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Mono for C# support (lightweight alternative to .NET SDK)
RUN gpg --homedir /tmp --no-default-keyring --keyring gnupg-ring:/usr/share/keyrings/mono-official-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF \
    && chmod +r /usr/share/keyrings/mono-official-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/mono-official-archive-keyring.gpg] https://download.mono-project.com/repo/debian stable-buster main" | tee /etc/apt/sources.list.d/mono-official-stable.list \
    && apt-get update \
    && apt-get install -y mono-devel mono-complete \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Go compiler (supports multiple .go files in same package)
ARG GO_VERSION=1.25.3
RUN wget https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz && \
    rm go${GO_VERSION}.linux-amd64.tar.gz && \
    ln -s /usr/local/go/bin/go /usr/bin/go && \
    ln -s /usr/local/go/bin/gofmt /usr/bin/gofmt

# Install Rust compiler (supports multiple .rs files with proper module structure)
ARG RUST_VERSION=1.90.0
ENV RUSTUP_HOME=/usr/local/rustup
ENV CARGO_HOME=/usr/local/cargo
ENV PATH=/usr/local/cargo/bin:$PATH
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain ${RUST_VERSION} --no-modify-path && \
    chmod -R a+rx /usr/local/rustup /usr/local/cargo

# Copy entire worker code into the container
COPY . .

# Make startup script executable
RUN chmod +x start-workers.sh

# Get environment variables to configure Redis connection
ENV REDIS_HOST=queue
ENV REDIS_PORT=6379
ENV REDIS_PREFIX=kodejudge
ENV WORKER_CONCURRENCY=4

# Command to run the workers with concurrency support
CMD ["./start-workers.sh"]
