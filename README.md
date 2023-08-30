# Hosts file updater for Fedora Linux

The `hosts` file is a great tool for safeguarding your online experience. A `hosts` file is the simplest and most efficient way to protect yourself against tracking codes embedded in web pages and shields you from offensive or malicious websites.

The purpose of  the `hosts` is to map hostnames to IP addresses and was initially created manually. The `hosts` table has been superseded by DNS (Domain Name System) which automated the publication process as the internet expanded. Today, the `hosts` file functions as an [alternative](https://www.man7.org/linux/man-pages/man5/hosts.5.html) name resolution mechanism within an operating system and is frequently used as an [Internet resource blocking](https://en.wikipedia.org/wiki/Hosts_(file)) tool.

The `hosts` file can serve as a simple yet very efficient if not radical outgoing network traffic firewall.

I started to use a `hosts` file as a defense against adware and malware during the mid-2000s. Marketers started inundating the internet with annoying animated GIFs and Flash ads. The barrage of ads made it challenging to focus on reading content. For a long time, I used [MVPS Hosts](https://winhelp2002.mvps.org/hosts.htm): a comprehensive and regularly updated `hosts` file. 

Today, I use [Steven Black](https://github.com/StevenBlack/hosts) unified `hosts` which filters [adware](https://www.fastcompany.com/90359992/an-ad-tech-pioneer-on-where-our-data-economy-went-wrong-and-how-to-fix-it), [trackers](https://www.fastcompany.com/90447583/our-collective-privacy-problem-is-not-your-fault), malware and offensive websites, very useful for parental control.

You can install a `hosts` file on any computing device, such as desktops, laptops, servers, routers.

Alternatively, you can integrate a `hosts` file into a browser extension like [uMatrix](https://addons.mozilla.org/en-US/firefox/addon/umatrix/) by Raymond Hill. This approach allows you to selectively enable ads on websites of your choice. 

A browser extension like uMatrix is also required to protects against trackers added to address links.

On mobile devices, you can use a browser like DuckDuckGo ([iOS](https://apps.apple.com/app/duckduckgo-privacy-browser/id663592361?pt=866401&mt=8), [Android](https://play.google.com/store/apps/details?id=com.duckduckgo.mobile.android)). But for comprehensive device-wide firewall protection, you need a VPN with filtering capabilities.

`updateHosts.py` is a one-click Python updater of the `hosts` file.

`test_updateHosts.py` is a unit test for `updateHosts.py`.

## Requirements
- Fedora Linux, RHEL and similar Linux distributions. 
- Python version 3.7 or later.

## Command-line usage

```sh
python updateHosts.py
```

To make the Python script executable, run:

```sh
chmod u+x updateHosts.py
```

Then 

```sh
./updateHosts.py
```

What it does:
1. Downloads the latest `hosts` file with all extensions from Steven Black GitHub repository.
2. Verifies the integrity of the `hosts` file.
3. (optional) Save to disk, update `/etc/hosts`  and restart `NetworkManager` to flush the DNS cache.

Alternatively, if you already have a `hosts` file and wish to use it, run:
```sh
./updateHosts.py <hosts-file>
```

Replace `<hosts-file>` with the path to your existing `hosts` file.

## Other updaters

Alternatively, you can explore the excellent `hosts` file [updater](https://github.com/StevenBlack/hosts/blob/master/updateHostsFile.py) available on Steven Black's GitHub repository.
It's a cross-platform (macOS, Unix, Linux, Windows) Python script with more options, including the ability to select extensions and use whitelists.
