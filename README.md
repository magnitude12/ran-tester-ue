# NTIA RAN Tester UE

This project is a UE centric RAN testing framework designed to quickly and easily test RANs against common attacks. The system works using declarative test configurations, which specify all the hardware and software needed to run complex series of security tests against a RAN.

See the our comprehensive [documentation ](https://docs.rantesterue.org) for more info on our attacks and metrics.

---

This RAN tester UE (rtUE) is fully software-based and compatible with widely available, commercial off-the-shelf (COTS) software radio hardware. Standardized 3GPP or O-RAN tests, as well as custom test procedures, can be implemented and executed at minimal cost and at different stages of RAN development and integration. This system facilitates testing across multiple commercial and open-source RAN implementations with minimal technical overhead. Additionally, many attacks on the RAN can be executed automatically by the system.

---

## System Requirements

### Machine and OS Recommendations

The RAN tester UE is tested on `Ubuntu 24.04`. However, any linux distro or MacOS machine should be able to run the software with few issues. If there are problems on these platforms, feel free to make an issue for us to address.

We recommend using the ubuntu realtime kernel, which is available for purchase from canonical. Alternatively, use can use the lowlatency kernel, which is free.

A powerful machine is recommended, since many of the attacks are resource intensive.

### Required Dependencies

Install the following on your system before running the system:
- docker engine
- docker compose
- UHD utilites (for downloading firmware images)

## Quickstart Guide

***First, clone the core repository***

```bash
git clone https://github.com/oran-testing/ran-tester-ue.git
```

***Navigate to the directory and run the system setup script:***
```bash
cd ran-tester-ue
./scripts/system_setup.sh
```

***Now, pull the system containers from our registry:***

```bash
sudo docker compose pull      # Grafana, InfluxDB, and Controller
```

Alternatively, you can build the images yourself:

```bash
sudo docker compose build
```

***Finally, modify the configuration to run a test:***

The test specification is defined in the YAML config (`ran-tester-ue/spec.yaml`):

This configuration tells the controller which services to run, and in what order. This allows for fully automated tests with many components.
```yaml
enable_cli: true

build_spec:
  - component: "sni5gect"
    docker_image: "ghcr.io/oran-testing/sni5gect"
    pull: false

run_spec:
  - component: "rtue"
    name: "rtue_uhd_1"
    config_file: "configs/srsran/ue_uhd.conf"
    rf:
      type: "b200"
  - component: "sni5gect"
    name: "downlink_sniffer"
    config_file: "configs/sni5gect/srsgnb_band3.yaml"
    rf:
      type: "b200"
```

The above configuration will run a sni5gect sniffer and UE with the requested environment, writing all data to influxdb and displaying metrics in realtime with grafana.

To start the system run:
```bash
sudo docker compose up
```

The Grafana dashboard can be accessed at [http://localhost:3300](http://localhost:3300).


## Nvidia Setup
Run the following command to setup docker to use the nvidia gpu
```bash
sudo ./scripts/nvidia_toolkit_setup.sh
```
