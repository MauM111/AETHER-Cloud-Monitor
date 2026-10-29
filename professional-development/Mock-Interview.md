# Mock Interview — Junior Cloud Engineer

**PFD200 professional development evidence**

This document contains five prepared interview questions and sample responses. A classroom mock interview activity was also completed, as described in the PFD200 portfolio. These written answers are preparation material, not a verbatim transcript or an independently graded interview.

## Question 1 — Tell me about yourself and why you want to become a Cloud Engineer.

I am currently completing Level 5 of my Computing studies and am working towards a career in cloud engineering. I have developed practical skills in Linux, Python, networking and troubleshooting through academic and personal projects. My main project, AETHER – Cloud Intelligence, helped me combine these skills in a working Linux monitoring application. I also have approximately ten years of experience in Health and Social Care, where I developed communication, accurate documentation and calm problem-solving under pressure. I want to bring those professional habits into a technical role and continue learning about cloud infrastructure and automation.

## Question 2 — Can you explain your AETHER project and what you contributed?

AETHER is a monitoring dashboard running on an Ubuntu virtual machine. I used Python and psutil to collect CPU, memory and disk metrics, Flask to provide the data, and JavaScript with Chart.js to display live and historical charts. I added CSV history, resource alerts and an incident timeline. I configured SSH access and a systemd service so the application could start after a reboot. I tested it by generating high CPU load, checking the critical alert and recovery, and testing connection loss. It is a learning prototype rather than a production cloud service, but it gave me hands-on experience of Linux operations and troubleshooting.

## Question 3 — A Linux monitoring service stops responding. How would you troubleshoot it?

First, I would confirm the symptoms and whether the virtual machine or host is reachable. I would check the service status with `systemctl status`, then inspect logs using `journalctl`. I would check whether the application is listening on the expected port and test the local API with `curl`. I would also check CPU, memory and disk utilisation and verify any SSH or port-forwarding configuration. I would change one thing at a time, record the result and retest. If the service needed restarting, I would investigate the cause rather than assume a restart had solved the underlying problem.

## Question 4 — What is the difference between running an application in a virtual machine and deploying it in the cloud?

My AETHER project runs in a local Ubuntu virtual machine using VirtualBox. A cloud deployment would use infrastructure provided by a cloud platform and introduce additional considerations such as identity and access management, virtual networks, firewall rules, monitoring costs, backups and availability. Some Linux and troubleshooting skills transfer directly, but I would not claim that a local VM project is the same as production cloud experience. My next learning goal is to deploy a small secured workload to a cloud virtual machine and document the process.

## Question 5 — What is one area you need to improve, and how will you do it?

My main development gap is hands-on experience with cloud services and infrastructure automation. I have a stronger foundation in Linux, Python and troubleshooting, but less practical experience with services such as AWS or Azure and tools such as Terraform. I plan to build a small cloud lab, document network and access-control settings, add automated tests to AETHER, and use GitHub to track progress. I would also seek feedback from more experienced engineers and be open about what I have not yet done.

## Preparation reflection

The strongest responses are those supported by practical evidence from AETHER: using `systemctl` and `journalctl`, testing alerts under CPU load, and explaining how Flask, Python and the dashboard interact. A key development area is hands-on public-cloud experience. Another is communicating technical work concisely: I should give a clear summary first, then expand when asked.



---


