---
# yaml-language-server: $schema=schemas/page.schema.json
title: "From PM2 to Systemd"
description: "Highlights reasons and steps taken to migrate a NodeJs project from PM2 to Linux systemd"
draft: false
date: "2026-05-20T21:00:00+01:00"
featured_image: ""
taxonomies:
  tag: Tag
_build:
  publishResources: false
Object type:
    - Page
Tag:
    - blog
    - work-log
    - article
    - mental-note
Creation date: "2026-05-20T12:46:37Z"
Created by:
    - ukor
Description: "Highlights reasons and steps taken to migrate a NodeJs project from PM2 to Linux systemd"
id: bafyreietd5zgqa6jggvfhafadynfjntznya3zwxupqsjwa3zscn27loasm
---

Every developer who has worked with the NodeJS environment will probably have heard of PM2. After building a NodeJS project, the big question arises, "How do I deploy this project to production?".    
   
If you are using a managed cloud provider, the answer is fairly simple, but if you are one of us building in a constrained environment or just someone who likes to host their own project, you will definitely hear about PM2. 

PM2 is a software that starts your application and manages the background process for you.    

## Why Leave PM2?   
PM2 has been great for us; it is simple and just requires a configuration file at the root of a project. However, it does a lot of work behind the scenes that will make scaling and debugging a NodeJS project a bit difficult.   
   
What makes PM2 great is the ability to use it ut of the box without any complex setup. With one command you see all your running program and with another you see the logs of all or each process running.   
This simplicity comes at a cost. Here is why we are leaving it:   
-  The silent death: We want to see the logs (stdout or stderr) as the process starts up.   
- PM2 introduces an extra tooling layer we have on production, but not in development   
- Extra memory cost for running PM2, while it is negligible, as time passes it has become important for us to account for every memory spent   
- Prevent crash loop, PM2 is configured to restart when the app crashes which floods the logs   
   
   
### The problem with `stdout`  and `stderr`  in PM2   
We repeatedly had these issues when starting our app with PM2. During startup, PM2 does not provide immediate feedback if something goes wrong.   
For example, when I run    
```bash
pm2 start app.js

```
   
PM2 still gives me a successful online status even if the start completely failed due to missing environment variable or a syntax error.    
   
This happens because PM2 operate like a detached daemon.  PM2 CLI hands over the file over to PM2 daemon and the daemon responds with a "successful got the file". The initial `stdout`  and `stderr`  streams are lost in the process which makes it impossible to know what went wrong.   
   
If you think running   
```
pm2 logs <app_name> --lines 1000
```
will give you a clue of what went wrong, you are wrong.   
   
If this is the first time you are starting the NodeJS app, you will get a blank/empty log. If it is not the first, you will get the log from the last time the app ran.   
   
Tailing the global PM2 log file does not help either   
```
tail -f ~/.pm2/pm2.log --lines 1000

```
This "silent death" became an unimaginable issue for us; it felt worst because we don't use PM2 in development to replicate it.   
## Hello, Systemd   
Before we switch to `systemd,` we need to highlight what we needed to achieved using systemd   
- Ability to access startup logs (stdout and stderr)   
- Ability to run clustered instance of the NodeJS app   
- Clean run time logging   
- Zero downtime during restart and deployment   
- Controlled, finite restart during application crashes   
- Horizontal scaling across CPU cores (this still falls under clustering)   
   
   
To use `systemd`, I defined a service configuration file written in `INI`  format at `/etc/systemd/system/my-app.service`   
   
```INI
[Unit]
Description=My Production Node.js Application
After=network.target

[Service]
Type=simple
User=nodeuser
Group=nodeuser

Environment=NODE_ENV=production
EnvironmentFile=/etc/my-app/.env

# Absolute paths are mandatory
WorkingDirectory=/var/www/my-app
ExecStart=/usr/bin/node /var/www/my-app/server.js

# Crash Recovery configuration
Restart=on-failure
# wait 5 seconds before restarting
RestartSec=5s
# if crashes are more than 3 times within a 60-second window, give up and leave it in a failed state
StartLimitIntervalSec=60s
StartLimitBurst=3
# restart if the app hits a memory threshold (cgroups control)
MemoryMax=1G 

# Redirecting logs out of generic syslog into isolated files
StandardOutput=append:/var/log/my-app/stdout.log
StandardError=append:/var/log/my-app/stderr.log

[Install]
WantedBy=multi-user.target
```
   
### Scaling and Cluster    
To achieve cluster and horizontally scaling across CPU cores, I use the  `systemd template` files by adding `@`  symbol to the service filename. `/etc/systemd/system/my-app@.service`

Systemd template files creates a reusable blueprint.   
Inside the file, I used the `%i`  specifier as a dynamic placeholder for port number.   
```INI
[Unit]
Description=App Instance on Port %i
After=network.target

[Service]
Type=simple
User=nodeuser
Environment=NODE_ENV=production PORT=%i
EnvironmentFile=/etc/my-app/.env
WorkingDirectory=/var/www/my-app
ExecStart=/usr/bin/node /var/www/my-app/server.js

Restart=always
RestartSec=3

# isolate logs per instance natively
StandardOutput=append:/var/log/my-app/stdout-%i.log
StandardError=append:/var/log/my-app/stderr-%i.log


[Install]
WantedBy=multi-user.target
```
`The %i` variable injects whatever string comes after the `@`  when the service is started using the `systemctl` CLI   
   
To start an instance, run the following   
```bash

# Enable them to start on boot
sudo systemctl enable my-app@3000 my-app@3001 my-app@3002 my-app@3003

# Start them all immediately
sudo systemctl start my-app@3000 my-app@3001 my-app@3002 my-app@3003
```
   
### Deployment Script   
We can achieve zero-down time during deployment by using a  bash script that restart all processes sequentially.    
   
```bash
#!/bin/bash
for port in 3000 3001 3002 3003; do
    echo "Deploying to port $port..."
    sudo systemctl restart my-app@$port
    sleep 2 # 2 second to boot up before moving to the next
done
```
   
### Node.JS native clustering   
I experimented with using NodeJS native cluster in the application code, but this introduce some drawbacks   
- systemd will only track the primary process, if a single worker crashes, systemd would not know since it relies on `cluster.on('exist')`  code to spawn.   
- There will be a brief period of downtime during deployment because `systemctl restart`  will kill the primary process, which will instantly destroy all workers.   
   
### Nginx, The Load Balancer   
I placed Nginx is in front of the node app. Nginx handles load balancing, rate limiting and also shift traffic away from app instance that down during sequential deployment by our script   
   
### Hardening and Privilege    
To tighten security, I created an unpriviledge, non-login user for this article, lets call the user `nodeuser` . nodeuser is responsible for running the application and reading file but never write.   
The application root folder was locked down using this permission   
```
# root or a login user owns the code, but the web group can read it
sudo chown -R root:www-data /var/www/my-app

# files are read-only for the group, hidden from everyone else
sudo find /var/www/my-app -type f -exec chmod 0640 {} \;

# directories allow navigation, and SGID (2) enforces group inheritance
sudo find /var/www/my-app -type d -exec chmod 2750 {} \;


```
   
If your node apps handle file upload, you may want to make an exception for a dedicated folder and grant ownership to the upload folder, something like   
```
sudo chown -R nodeuser:www-data /var/www/my-app/uploads
sudo chmod -R 2770 /var/www/my-app/uploads
```
   
Finally, to automate this I created an Ansible playbook that first set up the user, `nodeuser`  then another to write the systemd service files to proper folders.   
   
For deployment I use GitHub Actions, when we merge a PR or create a new tag a script evaluate which service was changed, evaluate the number of CPU cores in the target server and assign unique port sequentially.   
For example, if the auth service base port is 4190 for every CPU core, I add 1 (4190, 4191, 4192); this allow every instance to have unique port.   
## Why Not Just Use Docker   
Yes, Docker will save us this headache. Using Docker will remove the need for  PM2, as we can get all the benefits of PM2, including app restarts on crashes.   
   
Docker introduce another layer of complexity that I and the team are not ready for yet. Another learning curve, security and best practice.    
   
Most importantly, we have a strict budget for server cost and memory usage. You may sugest Podman as a lightweight alternative to Docker and it also have less memory footprint. Containerisation is an hard No for us as it increases the surface area we need to cover when it comes to system security.   
   
Sticking with systemd allow us to just focus on managing secrets and privilege escalation. Docker comes with a lot of checklist that we don't have the budget for.   
   
## Trade-offs and Future Improvement   
Although systemd solves most of our concerns, it also introduces a few pain points that should be addressed in the near future.   
### The Scaling Maintenace Burden   
Right now our deployment script evaluates the server CPU's core and automatically maps application instances.    
When we vertically scale a server by adding more cores, there is going to be a manual bottle neck; an engineer has to remember to update Nginx configuration file to include the new upstream ports.   

To resolve this manual step in the future, I plan to move towards a software like Traefik that allows dynamic configuration changes.   
   
### Monitoring, Dashboards, and Alert   
One of the benefits of using PM2 is that you can get the status, memory usage and number of restarts of all processes managed by PM2 using one command.    
PM2 also offer a web dashboard that can be accessed through the browser. The dashboard is not on by default, it has to be configured. This does not exist with systemd.    
To resolve this, I intend to    
- Use systemd timers to run a script that periodically run a status check across all the application instances   
- Parse the output of `systemctl status` , then pipe directly into a JSON file that will be served by Nginx   
- Use Slack or Telegram webhooks for alerting if any instance switch to failed state   
   
   
   
   
