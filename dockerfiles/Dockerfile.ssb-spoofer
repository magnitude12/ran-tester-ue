FROM ubuntu:24.04

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get upgrade -y && \
    apt-get install -y \
    cmake \
    make \
    gcc \
    g++ \
    pkg-config \
    libzmq3-dev \
    iproute2 \
    uhd-host \
    libgtest-dev \
    iperf3 \
    libfftw3-dev \
    libmbedtls-dev \
    libsctp-dev \
    libyaml-cpp-dev \
    net-tools \
    libboost-all-dev \
    libconfig++-dev \
    libxcb-cursor0 \
    libgles2-mesa-dev \
    gr-osmosdr \
    libuhd-dev

RUN mkdir -p /app

WORKDIR /app

COPY . .

RUN rm -rf build && mkdir -p build && cd build && cmake -DENABLE_ZEROMQ=ON .. && make -j$(nproc) && make install && ldconfig

CMD [ "ssb_spoofer", "--config", "/spoofer.yaml" ]
