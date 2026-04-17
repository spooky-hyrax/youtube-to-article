# How to Set Up a Kubernetes Home Lab on Bare Metal with Talos Linux

Setting up a Kubernetes home lab doesn't require expensive hardware or complex virtualization. With an old desktop computer and Talos Linux, you can have a fully functional Kubernetes cluster running in minutes. This guide walks you through the entire process, from downloading the ISO to deploying your first workload.

## Introduction

If you've been wanting to learn Kubernetes but thought you needed specialized equipment, think again. An old Dell desktop from 2011 can run Kubernetes perfectly fine. Talos Linux makes this incredibly easy because it's specifically designed to run Kubernetes on bare metal without all the complexity of traditional Linux distributions.

The machine used in this tutorial is a Dell Optiplex 9990, which is over 13 years old. You can find similar old desktops for under $100 depending on where you live and the specifications you need. The beauty of Talos is that it strips away everything unnecessary, leaving you with a purpose-built operating system that exists solely to run Kubernetes.

## Downloading the Talos ISO

The first step is getting the Talos ISO file that you'll use to boot your machine. Head over to talos.dev and navigate to the documentation section. Look for the Talos Linux Guides and find the installation dropdown. Since this is a bare metal installation with no virtualization involved, you'll want to select the ISO option.

There are two main flavors available: secure boot and standard BIOS. If you're working with newer hardware that supports UEFI and secure boot, you can use the image factory to create customized images with different layers and configurations. However, for older hardware that only has traditional BIOS support and no secure boot capabilities, you'll need the standard metal ISO.

To find this ISO, navigate to the Talos releases page on GitHub. Search for "metal AMD64" to filter the results, and you'll find the ISO file you need. Download this file to your local machine.

## Creating a Bootable USB Drive

Once you have the ISO downloaded, you need to put it on a USB drive. There are many different tools available for flashing ISOs to USB drives depending on your operating system. One particularly useful tool is Ventoy, which you can find at ventoy.net.

Ventoy works differently from traditional ISO flashing tools. Instead of extracting and rewriting the entire USB drive every time you want to use a different ISO, Ventoy acts as a manager for multiple ISOs. You simply install Ventoy on your USB drive once, and then you can copy ISO files directly onto it without any extraction or conversion.

With a 64GB USB drive, you can keep multiple ISOs ready to go at any time. Simply copy the Talos metal AMD ISO file to the Ventoy drive, and you're ready to boot. There's no need to extract anything or rewrite the drive—just drag and drop the file.

## Booting the Machine

With your USB drive prepared, it's time to boot the machine. Insert the USB drive into your target computer and power it on. Depending on your hardware, you may need to adjust the boot order or press a specific key (often F12) to access the boot menu.

Every machine is different, so you'll need to figure out the specific boot options for your hardware. Some machines let you set a temporary boot device, while others require you to enter the BIOS settings to change the boot order. For convenience, you might want to set USB as the first boot device if you plan on frequently testing different operating systems.

If you're using Ventoy, you'll be greeted with a menu showing all the ISOs on your drive. Select the Talos metal image you downloaded and choose to boot it in normal mode. The system will start loading Linux, go through a brief grub screen, and then begin the Talos boot process.

## Understanding the Talos Dashboard

When Talos finishes booting, you'll see the Talos dashboard on your screen. This is the local console interface that provides important information about your system's status.

The key things to note on this dashboard are the stage indicator in the top right corner, which will show "maintenance" mode when you first boot, and the IP address display. The IP address is critical because you'll need it to connect to this machine and configure it remotely.

It's worth understanding that Talos is completely API-driven. There's no shell access, no SSH, and no user accounts. Everything is done through the Talos API, which is why knowing your IP address is essential. In maintenance mode, Talos accepts certain queries without authentication, but once the system is installed and configured, all requests must be authenticated.

## Generating Configuration Files

Now you need to generate the configuration files that will define your Kubernetes cluster. Jump back to the Talos documentation and look at the getting started guide. The first command you'll run is `talosctl gen config`, which creates all the necessary files.

This command requires two main arguments: a cluster name and a cluster endpoint. The cluster name can be anything you want—something descriptive that helps you identify this cluster. The endpoint is the IP address of your node, formatted as an HTTPS URL with port 6443, which is the default Kubernetes API port.

For example, if your node's IP address is 192.168.6.47, your command might look like:

```
talosctl gen config delluster https://192.168.6.47:6443
```

This command generates several files: a secrets file containing your root of trust and tokens, a control plane configuration, a worker configuration, and a Talos config file. The Talos config file is what your `talosctl` command uses to communicate with nodes, while the control plane and worker files define the Kubernetes cluster configuration.

## Identifying the Installation Disk

Before applying the configuration, you need to know which disk to install Talos on. You can query this information from the machine while it's in maintenance mode.

Run the disks subcommand with the insecure flag:

```
talosctl disks --insecure -n 192.168.6.47
```

The insecure flag is necessary because you haven't installed Talos yet, and the machine is still in maintenance mode accepting unauthenticated queries. This command will show you all the available disks on the system, including their device paths and model names.

Look carefully at the output to identify your installation target. You might see something like `/dev/sda` which could be your USB drive (especially if the model shows something like "Data Traveler"), and `/dev/nvme0n1` which would be an internal NVMe drive. Make sure you select the correct disk—you don't want to accidentally overwrite your USB drive.

## Modifying the Control Plane Configuration

Now you need to edit the control plane configuration file to specify your installation disk. Open the `controlplane.yaml` file in a text editor and search for "dev/" to find the disk configuration section.

The default template typically shows `/dev/sda` as the installation target. Replace this with the correct path for your system. In this example, change it to `/dev/nvme0n1` to target the internal NVMe drive. Save the file after making this change.

This is a critical step—specifying the wrong disk could lead to data loss or failed installation. Double-check that you're pointing to the correct device before proceeding.

## Applying the Configuration

With your configuration files ready, it's time to apply them to the machine. Use the `apply config` command to send the configuration to your node:

```
talosctl apply config --insecure -n 192.168.6.47 -f controlplane.yaml
```

Again, you're using the insecure flag because the machine is still in maintenance mode. Once you run this command, watch the console—things happen quickly. The stage indicator will change from "maintenance" to "installing," and you'll see the cluster name appear on the dashboard.

The installation process involves writing Talos to the disk, setting up the necessary partitions, and preparing the system for Kubernetes. Once complete, the machine will automatically reboot to apply the new configuration.

After the reboot, you'll see the stage change to "booting" and then information about the Kubernetes version and components like kubelet, API server, controller manager, and scheduler will appear.

## Bootstrapping the Cluster

Even though Talos is installed, you still need to bootstrap the Kubernetes cluster. This step creates the etcd database that Kubernetes relies on for storing cluster state.

This time, you'll use an authenticated command because Talos has been installed and is no longer in maintenance mode:

```
talosctl bootstrap --nodes 192.168.6.47 --endpoints 192.168.6.47 --talosconfig talosconfig
```

The Talos config file you generated earlier contains the client-side certificates needed for authentication. Talos will no longer accept insecure requests—all communication must be properly authenticated.

Watch the console as you run this command. You'll see logs about containerd starting, etcd cluster initialization, and various Kubernetes components coming online. The stage will change to "running," though the ready state may initially show as false while everything finishes initializing.

## The Importance of Static IP Addresses

Here's a critical lesson that's easy to overlook: IP addresses can change during the setup process, especially if you're relying on DHCP. If your IP address changes between generating certificates and bootstrapping the cluster, you'll encounter connection errors.

If you see an "RPC unavailable" error when trying to connect to your node, check the console to see if the IP address has changed. In a home lab environment, you should definitely set up a DHCP reservation or static IP address for your machine before starting this process.

You have two options if your IP changes: either set up a reservation for the original IP address and ensure your certificates match, or reset the installation and start over with a stable IP configuration. To reset, boot from the USB drive again, select the Talos image, and choose the "reset installation" option from the grub menu. This wipes the drive and lets you start fresh.

The key takeaway is to configure a stable IP address before beginning the installation process. This ensures your certificates, configurations, and cluster endpoints all remain consistent.

## Monitoring the Installation

Talos provides several ways to monitor what's happening during and after installation. The `talosctl dashboard` command gives you a terminal-based UI that mirrors the console dashboard:

```
talosctl dashboard --nodes 192.168.6.47 --endpoints 192.168.6.47 --talosconfig talosconfig
```

This view shows you the stage (running, booting, maintenance), health status of various components, and whether the node is ready. You can also stream logs directly to your terminal:

```
talosctl logs --follow -n 192.168.6.47 --endpoints 192.168.6.47 --talosconfig talosconfig etcd
```

This command follows the etcd service logs, letting you see exactly what's happening with the cluster database. You can replace "etcd" with any other service name to monitor different components.

Another useful command is the services subcommand:

```
talosctl services --nodes 192.168.6.47 --endpoints 192.168.6.47 --talosconfig talosconfig
```

This shows all services running in the cluster along with their health status. You'll see the Talos API, containerd, the CRI dashboard, and all the Kubernetes components listed with their current state.

## Getting the Kubernetes Config

Once your cluster shows as ready (you'll see healthy status for kubelet, API server, controller manager, and scheduler), you can retrieve your Kubernetes configuration file:

```
talosctl kubeconfig --nodes 192.168.6.47 --endpoints 192.168.6.47 --talosconfig talosconfig ./kubeconfig
```

Export this configuration so kubectl can use it:

```
export KUBECONFIG=./kubeconfig
```

Now you can interact with your cluster using standard Kubernetes commands:

```
kubectl get nodes
```

You should see your single node listed as a control plane node with its Kubernetes version.

## Enabling Workloads on the Control Plane

By default, Kubernetes doesn't allow regular workloads to run on control plane nodes. This is a good security practice for production clusters, keeping the control plane isolated from application workloads. However, with a single-node home lab cluster, you need to run everything on the same machine.

To enable workload scheduling on your control plane node, you need to modify the configuration. Check the Talos documentation for "enable workers on control plane" to find the exact setting.

In your `controlplane.yaml` file, look for the `allowSchedulingOnControlPlanes` setting. It's typically commented out by default. Uncomment it and set it to `true`:

```yaml
allowSchedulingOnControlPlanes: true
```

Apply the updated configuration:

```
talosctl apply config --nodes 192.168.6.47 --endpoints 192.168.6.47 --talosconfig talosconfig -f controlplane.yaml
```

The configuration applies without requiring a reboot. Now you can deploy workloads to your single-node cluster.

## Deploying Your First Workload

Test your cluster by deploying a simple application. Create a basic nginx deployment:

```
kubectl create deployment nginx --image=nginx
```

Check that the pod is running:

```
kubectl get pods -o wide
```

You should see the nginx pod running on your control plane node. Before enabling workload scheduling, this deployment would have remained pending because no nodes were available to run it. Now your single-node cluster is fully functional and ready to host applications.

## Conclusion

Even with a brief detour to handle the IP address issue, setting up a Kubernetes cluster on bare metal with Talos Linux is remarkably straightforward. The entire process involves downloading an ISO, creating a bootable USB, generating configurations, and running a few commands.

The beauty of this setup is its simplicity and resource efficiency. That old desktop or laptop sitting in your closet can become a learning platform for Kubernetes without any complex setup or expensive cloud bills. You now have a real Kubernetes cluster running on bare metal, ready for experimentation and learning.

If you want to expand your cluster later, you can add more worker nodes using the same process with the worker configuration file instead of the control plane configuration. For now, you have everything you need to start exploring Kubernetes on your own hardware.