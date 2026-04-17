# How to Set Up a Kubernetes Home Lab on Bare Metal with Talos Linux

Setting up a Kubernetes home lab doesn't require expensive enterprise hardware or complex virtualization setups. With an old desktop computer and Talos Linux, you can have a fully functional Kubernetes cluster running in minutes. This guide walks you through the entire process of transforming spare hardware into a powerful learning environment for container orchestration.

## Introduction

Talos Linux offers the easiest path to getting Kubernetes running on bare metal hardware. Unlike traditional Linux distributions that require extensive configuration, Talos is purpose-built for Kubernetes and eliminates much of the complexity typically associated with cluster setup.

For this project, an old Dell Optiplex 9990 from 2011 serves as the demonstration hardware. These types of desktops are readily available for under $100 depending on location and specifications. Despite being over a decade old, this machine runs Kubernetes without any issues, proving that you don't need cutting-edge hardware to start your Kubernetes journey.

## Downloading the Talos ISO

The first step involves obtaining the Talos ISO from the official website. Navigate to talos.dev and access the documentation section, then find the Talos Linux Guides. Under the installation dropdown, select the bare metal platform option since this setup doesn't involve any virtualization—just a direct installation onto hardware.

Several installation methods exist, including PXE booting environments for more established setups. However, for a straightforward home lab, the ISO method works perfectly. Simply download the ISO, write it to a USB drive, and boot from it.

Two flavors are available: secure boot and standard BIOS. For older hardware like the 2011 Dell desktop that lacks UEFI support and relies on traditional BIOS, the standard metal ISO is the appropriate choice. The secure boot option through the image factory creates images with different layers, but older machines typically don't support these modern security features.

To find the correct ISO, navigate to the Talos releases page on GitHub. Search for "metal AMD 64" to locate the appropriate ISO file for standard x86-64 architecture systems, then download it.

## Creating a Bootable USB Drive

Once downloaded, the ISO needs to be transferred to a USB drive. Various tools exist for flashing ISOs depending on your operating system. Ventoy stands out as a particularly useful option because it acts as a manager for multiple ISOs on a single flash drive.

With Ventoy installed on a USB drive, you don't need to extract and rewrite the drive every time you want to boot a different operating system. Simply copy ISO files directly onto the drive. A 64GB USB drive can hold numerous ISOs simultaneously, and Ventoy presents a menu at boot time allowing selection of which ISO to use.

After copying the Talos ISO to the Ventoy-prepared USB drive, it's ready for booting the target system.

## Booting the System

Insert the USB drive into the target machine and power it on. Depending on the hardware configuration, you may need to adjust boot settings to prioritize USB booting. Most systems offer a key like F12 during POST to access a temporary boot menu, or you can enter BIOS setup to change the permanent boot order.

For machines used frequently for testing different operating systems, setting USB as the first boot device saves time. When the system boots from the Ventoy USB drive, a menu appears listing all available ISOs. Select the Talos metal image and boot it in normal mode.

If everything proceeds correctly, Linux begins loading. A grub screen appears briefly before transitioning to the actual boot process. This can be monitored through a directly connected monitor or, for headless setups, through remote management tools like a Tiny Pilot.

## Understanding the Talos Dashboard

When Talos finishes booting, the dashboard screen appears. This local console provides essential information about the system state. The most critical pieces of information at this stage are:

**Stage Indicator**: Located in the top right corner, this shows "maintenance" mode, indicating the system is ready for configuration but hasn't been installed yet.

**IP Address**: Displayed across from the stage indicator, this address is essential for connecting to the machine remotely. In this example, the machine received 192.168.6.47 via DHCP.

Talos operates entirely through an API—there's no shell access, no SSH, and no user accounts. All configuration happens by sending commands to this IP address from another machine on the network.

## Generating Configuration Files

With the target machine running and its IP address known, configuration generation happens from a workstation with the Talos control utility installed. The getting started guide in the documentation provides all necessary commands.

The configuration generation command follows this pattern:

```
talosctl gen config [cluster-name] https://[IP-address]:6443
```

For this example, the cluster is named "duster" (a play on the Dell desktop) and uses the IP address obtained from the dashboard. The HTTPS protocol and port 6443 are specified because Talos secures all communication with TLS certificates, and 6443 is the standard Kubernetes API port.

Running this command generates several important files:
- **Secrets file**: Contains the root of trust and authentication tokens
- **Control plane YAML**: Configuration for control plane nodes
- **Worker YAML**: Configuration for worker nodes
- **Talos config**: Client configuration enabling the talosctl command to communicate with nodes

## Identifying the Installation Disk

Before applying the configuration, the target disk for installation must be identified. Talos provides a way to query this information from a machine in maintenance mode using the insecure flag, which is only accepted before the machine has been secured and locked down.

```
talosctl disks --insecure --nodes [IP-address]
```

This command returns information about available disks, including their device paths and model names. In the example setup, two disks appear:
- `/dev/nvme0n1` - An NVME drive internal to the system
- `/dev/sda` - A "Data Traveler" which is actually the USB boot drive

Identifying the correct disk is crucial to avoid accidentally overwriting the boot media. The USB drive's model name makes it easily identifiable, leaving the NVME drive as the correct installation target.

## Modifying the Control Plane Configuration

The generated control plane configuration uses `/dev/sda` as the default installation target. This needs modification to specify the correct NVME drive instead.

Open the control plane YAML file and search for "dev/" to locate the disk specification. Change the value from `/dev/sda` to `/dev/nvme0n1` (or whatever the appropriate device path is for your system).

This simple edit ensures Talos installs to the intended disk rather than attempting to overwrite the USB boot drive.

## Applying the Configuration

With the configuration modified, apply it to the machine in maintenance mode:

```
talosctl apply-config --insecure --nodes [IP-address] --file controlplane.yaml
```

The insecure flag is necessary because the machine hasn't yet been configured with the certificates that would normally authenticate requests. Upon applying the configuration, the dashboard immediately reflects changes—the stage transitions to "installing" and the cluster name appears.

The installation process proceeds quickly: Talos writes itself to the specified disk, then automatically reboots. After the reboot, the machine enters a "booting" stage, now running from the installed disk rather than the USB drive.

## The Importance of Static IP Addresses

A critical consideration emerged during this setup: DHCP-assigned IP addresses can change between reboots. The original IP address (192.168.6.47) changed to a different address (192.168.6.55) after the installation reboot.

This creates problems because:
- The generated certificates reference the original IP address
- The configuration files specify the original endpoint
- Commands targeting the old IP address will fail with "RPC unavailable" errors

**Solution**: Before beginning installation, configure a DHCP reservation on your router for the target machine's MAC address. This ensures the machine always receives the same IP address regardless of reboots.

If the IP address changes during setup, two options exist:
1. Create a DHCP reservation for the original IP address
2. Reset the Talos installation, create a reservation for a preferred IP, and reinstall

To reset an installation, boot from the USB drive again and select "Reset Talos installation" from the grub menu. This wipes the disk and returns the machine to a fresh state for reconfiguration.

## Bootstrapping the Cluster

Once the machine has a stable IP address and the configuration has been applied, the final step creates the etcd database that Kubernetes requires. This is called bootstrapping.

```
talosctl bootstrap --nodes [IP-address] --endpoints [IP-address] --talosconfig talosconfig
```

Unlike previous commands, this one doesn't use the insecure flag. After installation, Talos only accepts authenticated requests using the certificates generated earlier. The talosconfig file provides these credentials.

The bootstrap command triggers a flurry of activity visible in the logs—containerd starts, static pods for the API server are rendered, and the etcd cluster initializes. The dashboard stage transitions from "booting" to "running," though the ready state initially shows "false" while components spin up.

## Monitoring Cluster Progress

Several methods exist for monitoring the cluster as it comes online:

**Dashboard Command**: Running `talosctl dashboard` with the appropriate node and config flags provides the same interface as the local console, making it easier to monitor from a workstation.

**Log Streaming**: The command `talosctl logs -f --service etcd` streams etcd logs in real-time, showing database initialization progress.

**Service Status**: Running `talosctl services` lists all services and their health status, including the Talos API, containerd, kubelet, and etcd.

As services become healthy, the dashboard's ready state eventually changes to "true," indicating the Kubernetes cluster is operational.

## Obtaining Kubernetes Access

With the cluster running, generate a kubeconfig file for kubectl access:

```
talosctl kubeconfig --nodes [IP-address] --endpoints [IP-address] --talosconfig talosconfig ./kubeconfig
```

Export the kubeconfig path and verify cluster access:

```
export KUBECONFIG=./kubeconfig
kubectl get nodes
```

The output shows the single node running as a control plane with the installed Kubernetes version.

## Enabling Workload Scheduling on the Control Plane

By default, Kubernetes prevents scheduling regular workloads on control plane nodes—a sensible separation for production environments. However, with only one machine in the cluster, this restriction would prevent running any applications.

The Talos documentation explains how to enable workload scheduling on control plane nodes. The control plane YAML file includes a commented-out option:

```yaml
cluster:
  allowSchedulingOnControlPlanes: true
```

Uncomment this line and reapply the configuration:

```
talosctl apply-config --nodes [IP-address] --endpoints [IP-address] --talosconfig talosconfig --file controlplane.yaml
```

The configuration applies without requiring a reboot. Now the node accepts regular pod scheduling.

## Deploying a Test Workload

To verify workload scheduling functions correctly, deploy a simple nginx application:

```
kubectl create deployment nginx --image=nginx
```

Checking the pods shows nginx running successfully on the control plane node:

```
kubectl get pods -o wide
```

The pod schedules and runs on the only available node in the cluster, confirming that the untainting worked correctly.

## Conclusion

Despite a brief detour to configure static IP addressing, the entire process of installing Talos and bootstrapping a Kubernetes cluster completes quickly. The old desktop that might otherwise collect dust in a closet now runs a fully functional Kubernetes environment.

This single-node cluster provides an excellent learning platform for Kubernetes concepts. The same process extends to multi-node setups—adding more workers involves booting additional machines from the same USB drive and applying worker configurations instead of control plane configurations.

Talos Linux removes much of the traditional complexity from Kubernetes bare metal installation. There's no need to configure container runtimes, install kubeadm, or manage system packages. The immutable, API-driven nature of Talos creates a consistent, repeatable deployment experience.

For anyone with spare hardware available, this approach offers a low-cost entry point into hands-on Kubernetes experience. Start with that old desktop or laptop sitting in a closet and begin exploring container orchestration in your own home lab.