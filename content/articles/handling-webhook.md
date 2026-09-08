---
# yaml-language-server: $schema=schemas/page.schema.json
title: "Handling Webhook Reliably"
description: "Handling webhooks with a highly reliable ingress layer (Inngest) in a fast paced environment"
draft: false
date: "2026-09-08T12:27:22+01:00"
featured_image: ""
taxonomies:
  tag: Tag
_build:
  publishResources: false
Object type:
    - Page
Tag:
    - work-log
    - blog
    - article
Creation date: "2026-09-08T10:17:23Z"
Created by:
    - ukor
Description: Handling webhooks with a highly reliable ingress layer (Inngest)
Emoji: ⛺
Cover image or color: teal
id: bafyreibqpivyudjqdqfadutvsz6l36ipqnqac36buoaiknkz7bxcnpzxt4
---
   
> It is really amazing how simple things are powered by complex processes    

   
Webhook request handling is not something I have paid too much attention to.   

Naively, my implementation flow was:   
-  create a post endpoint and submit it to the requesting platform,    
- verify the signature of the request    
- Call business logic and    
- Persist the result.   
   
This worked until my team and I  started experiencing network failures and we also started losing data; which we have to correct by manually reconciling data.   
   
To fix this, I introduce message queue; The web-hook no longer handles business logic but rather   
- receive webhook request   
- verify the signature; and    
- push it to the queue   
   
   
This solves the issue for data loss; but put another burden on the team: making sure the compute that handles webhook request is always up (durable) and has the ability to pickup from where it left off after downtime.   
   
Events like payments notification can never be dropped or lost.   
   
Normally we solved this by creating an edge function whose sole responsibility was to process webhook request from payment providers. But this does not totally solve the issues about data lost.   
   
The message broker itself can be offline for any reason, so I have to reason about    
- Error handling    
- Retries   
- Guaranteeing "exactly-once" delivery semantics   
- Graceful degradation   
   
   
These are all doable but not something the team would love to spend time on while the core product is still not fully implemented.   
   
I recently learnt about [Inngest](https://www.inngest.com/) and it has completely changed how I handle events my application especially for product we are building fast.   
   
## How Inngest helped   
- Inngest receives webhook notification and then triggers functions, we don't have to worry about managing another infrastructure for durable execution   

- Inngest keeps track of all failed processing, and present a nice dashboard for monitoring and retrying. Which also means that we can now replay events.  

- Inngest guarantees exactly-once processing and at-least-once delivery - It is up to us to make it exactly once by checking that the event has not been processed previously.   
   
Although Inngest can publish to multiple functions, we have limited it to sending data to our Message broker as the message broker is an integral part of our architecture and allows us to improve or build our own durable system if the need ever arises.   

