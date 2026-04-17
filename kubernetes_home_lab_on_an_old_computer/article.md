# How to Set Up a Kubernetes Home Lab on Bare Metal with Talos Linux

Setting up a Kubernetes cluster at home doesn't require expensive hardware or complicated virtualization setups. With an old desktop computer and Talos Linux, you can have a fully functional Kubernetes environment running in minutes. This guide walks you through the entire process of transforming spare hardware into a powerful learning and development platform.

## Introduction

If you've been wanting to learn Kubernetes but felt intimidated by the setup process, this guide is for you. We're going to set up a Kubernetes home lab using bare metal—an actual physical machine with real hardware—rather than virtual machines or cloud resources.

The secret weapon for this project is Talos Linux, which is arguably the easiest way to get Kubernetes running on bare metal. Talos is a purpose-built operating system designed specifically for running Kubernetes, and it eliminates much of the complexity traditionally associated with cluster setup.

For this demonstration, we're using an old Dell Optiplex 9990 desktop from 2011. The beauty of this approach is that you can find similar old desktops for under $100, depending on where you live and the specifications you need. Despite being over a decade old, this machine will run Kubernetes without any problems. If you have an old desktop or laptop gathering dust in a closet, this is the perfect opportunity to put it to good use.

## Downloading the Talos ISO

The first step is obtaining the Talos Linux ISO file that we'll use to boot and install the operating system. Head over to talos.dev and navigate to the documentation section, then find the Talos Linux Guides.

Under the installation dropdown, you'll find options for bare metal platforms. Since we're not using any virtualization and just want to install directly onto hardware, we need to choose the appropriate installation method. While there are options for PXE booting and other enterprise deployment methods, we're going with the straightforward ISO approach—download an ISO, put it on a USB drive, and boot from it.

You'll notice there are different flavors available, including secure boot options through the image factory, which can create customized images with different layers and configurations. However, for older hardware like our 2011 desktop, we need the standard old-school BIOS metal ISO. This particular machine doesn't even have UEFI—it's running a traditional BIOS with no secure boot capability, though there might be some TPM support.

To get the correct ISO, navigate to the Talos releases page on GitHub. You'll find numerous artifacts available for download, but since we're installing on metal, search for "Metal AMD 64" to find the appropriate ISO file. Download this file to your computer.

## Creating a Bootable USB Drive

Once the ISO is downloaded, we need to transfer it to a USB drive. There are various tools available for flashing ISOs depending on your operating system, but one particularly useful option is Ventoy.

Ventoy, available at ventoy.net, functions as a manager for ISOs on your flash drive. The advantage of using Ventoy is that you don't need to extract or rewrite the flash drive every time you want to use a different ISO. Instead, you install Ventoy once on your USB drive, and then you can simply copy ISO files directly onto it.

For example, with a 64GB USB drive running Ventoy, you can store multiple ISOs simultaneously. Simply copy the Talos 1.67 metal AMD ISO file into the Ventoy partition—that's all there is to it. The ISO remains intact, and when you boot from the USB drive, Ventoy presents a menu allowing you to select which ISO to boot.

This approach is especially convenient if you frequently work with different operating systems or need to reinstall systems regularly. You can maintain a collection of ISOs on a single USB drive without constantly reformatting it.

## Booting and Initial Configuration

With the USB drive prepared, insert it into your target machine and power it on. The system needs to boot from the USB drive, which may require adjusting your BIOS settings or using a boot menu.

Most systems have a key (commonly F12, F2, or Delete) that you can press during startup to access boot options. In this case, F12 provides access to a temporary boot device selection menu. If you plan to frequently boot from USB, you might want to set the USB drive as the first boot device in your BIOS settings.

Once the machine boots from USB, if you're using Ventoy, you'll see a menu displaying all the ISOs stored on the drive. Select the Talos 1.67 metal image that you downloaded and choose to boot it in normal mode.

If everything goes well, the system will begin booting. You'll see Linux loading, followed by a brief grub screen, and then the system will proceed to the Talos boot process. You can monitor this through a connected monitor or, for more advanced setups, through a KVM-over-IP device like TinyPilot.

When the boot process completes, you'll arrive at the Talos dashboard—the local console interface. The key information to note here is displayed in the top right corner: the system is in "maintenance mode," which indicates it's ready for initial configuration but hasn't been fully set up yet.

The most critical piece of information on this screen is the IP address, displayed across from the stage indicator. In this example, the system received IP address 192.168.6.47 via DHCP. You'll need this IP address to connect to the machine and configure it, since Talos is entirely API-driven—there's no shell access, no SSH, and no user accounts in the traditional sense.

## Generating Configuration Files

With the machine booted and its IP address noted, it's time to generate the configuration files needed to transform this machine into a Kubernetes cluster. This step is performed from your workstation, not from the machine being configured.

Refer to the Talos documentation's getting started guide, which outlines all the necessary steps. You'll need the Talos control command-line tool (talosctl) installed on your workstation.

The configuration generation command follows this pattern:

```
talosctl gen config <cluster-name> https://<ip-address>:6443
```

For this example, we're naming the cluster "duster" (a playful nod to it running on a Dell) and using the IP address of our node. The endpoint URL includes HTTPS because Talos secures all communications with TLS certificates, and port 6443 is the default Kubernetes API server port.

Running this command generates several important files:
- **Secrets/certificates**: The root of trust for your cluster, including various tokens
- **controlplane.yaml**: Configuration for control plane nodes
- **worker.yaml**: Configuration for worker nodes
- **talosconfig**: Client configuration that allows talosctl to communicate with your nodes

The talosconfig file is particularly important as it contains the client-side certificates needed for authenticated communication with the cluster.

## Identifying the Installation Disk

Before applying the configuration, we need to determine which disk Talos should use for installation. This is crucial to avoid accidentally overwriting the wrong drive—particularly the USB drive you're booting from.

Use the disks subcommand to query the available storage devices:

```
talosctl disks --insecure --nodes <ip-address>
```

The `--insecure` flag is necessary because we're communicating with a node that's still in maintenance mode and hasn't been configured with certificates yet. This is the only time Talos accepts unauthenticated requests—once the system is installed and secured, all commands require proper certificate authentication.

The output shows all detected storage devices with their device paths (like /dev/nvme0n1 or /dev/sda) and model information. This model information helps identify each drive. For example, if you see a "DataTraveler" in the model column, that's likely your USB drive, which you definitely don't want to use as the installation target.

In our case, we identified /dev/nvme0n1 as the internal NVMe drive—the appropriate target for installation. The USB drive appeared as /dev/sda with a DataTraveler model designation.

Now we need to modify the control plane configuration to specify this disk. Open the controlplane.yaml file in your preferred editor and search for "dev/" to find the disk specification. The default template typically shows /dev/sda as the installation target. Change this to match your identified disk—in this case, /dev/nvme0n1.

## Applying the Configuration

With the configuration files generated and the disk path corrected, it's time to apply the configuration to the machine. This step sends the configuration to the machine's API and instructs it to perform the installation.

Use the apply-config command:

```
talosctl apply-config --insecure --nodes <ip-address> --file controlplane.yaml
```

Again, the `--insecure` flag is required because we're still in maintenance mode. The command sends the control plane configuration to the specified node.

Upon applying the configuration, the machine immediately begins the installation process. If you watch the console, you'll see the stage indicator change from "maintenance" to "installing," and the cluster name will appear in the dashboard. The installation process writes Talos to the specified disk and configures the system.

Once installation completes, the machine automatically reboots. After the reboot, you'll see new information in the dashboard, including the Kubernetes version being deployed and the status of various components like kubelet, API server, controller manager, and scheduler.

At this point, the stage indicator shows "booting" as the system initializes. The ready state will initially show "false" while components start up.

## Bootstrapping the Cluster

The installation has placed Talos and the Kubernetes components on the machine, but one crucial step remains: bootstrapping the etcd database. etcd is the distributed key-value store that Kubernetes uses to store all cluster state, and it must be initialized before the cluster becomes functional.

Run the bootstrap command:

```
talosctl bootstrap --nodes <ip-address> --endpoints <ip-address> --talosconfig ./talosconfig
```

Notice that we're no longer using the `--insecure` flag. Talos has completed its installation and now requires authenticated requests. The talosconfig file we generated earlier provides the client-side certificates for authentication.

After running the bootstrap command, watch the console or use the talosctl dashboard command for a cleaner view of the startup process. You'll see containerd starting, etcd initializing, and then the various Kubernetes components coming online.

The stage indicator will transition from "booting" to "running," and eventually the ready state will change to "true" as all health checks pass. You can also monitor progress using:

```
talosctl logs --follow --nodes <ip-address> --talosconfig ./talosconfig etcd
```

This streams the etcd logs directly to your terminal, allowing you to watch the database initialization in real-time.

Additionally, you can check the status of all system services:

```
talosctl services --nodes <ip-address> --talosconfig ./talosconfig
```

This displays the health status of the Talos API, containerd, CRI, kubelet, etcd, and all other system services.

## Handling IP Address Changes

During this setup, you might encounter an issue where the machine's IP address changes between reboots. This is a common problem when relying on DHCP in home lab environments.

If you try to run commands and receive an "RPC unavailable" error pointing to the original IP address, check the console—the machine may have received a new IP address from your DHCP server.

There are two ways to address this:

1. **Set a DHCP reservation**: Configure your router or DHCP server to always assign the same IP address to this machine's MAC address. This is the recommended approach for any home lab setup.

2. **Reinstall with the new IP**: If the IP changed mid-setup, you can reset Talos and start over. Boot from the USB drive again, and at the grub menu, select the option to reset the Talos installation. This wipes the disk, allowing you to reconfigure with the correct (reserved) IP address.

For long-term stability, always configure a static IP address or DHCP reservation before beginning the setup process. The IP address is embedded in the generated certificates and configuration files, so consistency is essential.

## Enabling Workloads on the Control Plane

By default, Kubernetes doesn't allow regular workloads to run on control plane nodes—this is a security and stability best practice for production environments. However, with a single-node home lab cluster, you'll want to run workloads on your only available node.

The Talos documentation explains how to enable this. You need to modify the control plane configuration to include:

```yaml
cluster:
  allowSchedulingOnControlPlanes: true
```

Open your controlplane.yaml file and add or uncomment this setting (it may already be present but commented out in the default template, typically near the end of the file).

Apply the updated configuration:

```
talosctl apply-config --nodes <ip-address> --endpoints <ip-address> --talosconfig ./talosconfig --file controlplane.yaml
```

The configuration applies without requiring a reboot. This removes the taint that prevents workloads from being scheduled on control plane nodes.

## Accessing Your Cluster

With the cluster fully operational, you'll want to obtain a kubeconfig file to interact with Kubernetes using standard tools like kubectl.

Generate the kubeconfig:

```
talosctl kubeconfig --nodes <ip-address> --endpoints <ip-address> --talosconfig ./talosconfig ./kubeconfig
```

Export the kubeconfig path so kubectl can find it:

```
export KUBECONFIG=./kubeconfig
```

Now you can use standard kubectl commands:

```
kubectl get nodes
```

This should show your single node with the "control-plane" role and the Kubernetes version.

To verify that workloads can run on your control plane node, deploy a test application:

```
kubectl create deployment nginx --image=nginx
```

Check that the deployment is running:

```
kubectl get pods -o wide
```

The nginx pod should be running on your single node, confirming that the scheduling configuration is working correctly.

## Conclusion

Even with a brief detour to handle the IP address change issue, we successfully completed multiple Talos installations and set up a fully functional Kubernetes cluster. The entire process demonstrates how accessible Kubernetes can be when using the right tools.

Your home lab cluster is now ready for use. You can deploy applications, experiment with Kubernetes features, and learn container orchestration on real hardware. If you want to expand your cluster in the future, you can add more worker nodes using the worker.yaml configuration file generated earlier—that's a topic for another guide.

The key takeaway is that you don't need expensive equipment or complex infrastructure to start learning Kubernetes. That old desktop or laptop sitting in your closet can become a valuable learning platform. With Talos Linux handling the operating system complexity, you can focus on what matters: understanding and mastering Kubernetes itself.