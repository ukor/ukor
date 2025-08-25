---
# yaml-language-server: $schema=schemas/page.schema.json
title: "Building a Real-Time User Presence System"
description: "Building a Real-Time User Presence System: A Technical Deep Dive"
draft: false
date: "2025-08-24T05:05:46Z"
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
Creation date: "2025-08-24T05:05:46Z"
Created by:
    - ukor
Links:
    - User Presence(online|offline) Functionality
Emoji: "\U0001F7E2"
Cover image or color: green
id: bafyreifwd4szq4yvvoyg2mhzpmfx5h3vxwi5k5xnw4dfob235hbovhapoq
---

In this article, I intend to describe how I built a system for tracking users online presence.    
Users in this case are dispatch riders that operate as last-mile deliveries.   
For the backend to accurately dispatch tasks, it must know which riders are online, where they are and how long they have been active.   
This article focuses on how I solve the presence(online or offline) issue.

## Keeping Riders Online   
It is a simple but effective presence system. The rider app sends a ping(an HTTP patch request) to the backend every 15 minutes with their current location and presence status.   
This interval is key to balancing real-time accuracy and to also respect the iOS background fetch limit.   
For an Android device, the ping(hearth-beat) request is sent every 10 minutes.    
A rider is considered online if the backend has received a ping from them within the last 15 minutes. If a ping does not arrive on time, or if the rider explicitly goes offline status is updated accordingly  

### Transforming Location Data   
The rider app sends latitude and longitude in a raw format    
```json
{
  "latitude": 0.0,
  "longitude": 0.0,
}
```
To enable fast lookups and proximity base searches(like finding the nearest available rider), I transform the location data before storage.   
The simple location object is transformed into a more structured `GeoPoint`  format.

```json
{
  "type": "Point",
  "coordinates"": [longitude, latitude],
  "text": "uber-h3-hash"
}
```
A crucial part of this transformation is the inclusion of the Uber H3 hash. We will hash the rider's location, creating a unique string that represents a specific hexagonal area on the map. This allows us to perform fast approximate proximity queries by simply comparing hash strings, before resorting to more computationally expensive distance calculations.   
### Managing Online and Offline Status   
The backend manages a rider's status using a field called `lastSeen` . The value of this field will be a Unix timestamp in microseconds.   
### Online Presence   
When the backend receives a ping with an **online** status, it updates the rider's record. To ensure the rider remains "online" for the full 15-minute interval, we will set the value of the `lastSeen` field to a point in the future, the **current time plus 15 minutes**. As long as the rider's app continues to send pings every 10 to 15 minutes, their `lastSeen` value will always be in the future, and they will consistently be marked as online.   
### Offline Presence   
A rider can go **offline** in one of two ways:    
- They can explicitly send a ping with an offline status, or;    
- The backend can infer they're offline if a 15-minute ping is missed.    
   
In either case, we update the `lastSeen` timestamp to the **current time**. This ensures that the rider's `lastSeen` value is no longer in the future and that they are correctly filtered out of any "active" rider searches.   
## Active Time Puzzle   
One of the most important metrics for a rider's performance is their active time. This is the total time a rider was available to take trips. Our 15-minute ping interval means we don't have a constant stream of data, but we can still calculate an approximate active time.   
When a new ping arrives, we calculate the time elapsed since the `lastSeen` timestamp of the previous ping. We'll call this `time_diff`.   

$$
timeDiff = now - lastSeen

$$
 We then use this to update the rider's total active time. The key is to cap the calculated active time between pings at our maximum interval, which is **15 minutes (or 900,000 milliseconds)**.   
The rider is online if `timeDiff`  is less than `900000` milliseconds.   
   
For example, take our ping interval as 15 minutes. If a rider's last ping was at 1:00 PM and the current ping arrives at 1:10 PM, the `time_diff` is 10 minutes. Since this is less than 15 minutes, we add the full 10 minutes to their total active time. If the next ping arrives at 1:20 PM, the `time_diff` from the last ping is 10 minutes, and we again add 10 minutes. But what if the next ping doesn't arrive until 1:30 PM (a 20-minute gap)? In this case, the `time_diff` is 20 minutes, which is greater than our 15-minute cap. The system would only add **15 minutes** to their total active time, as that's the maximum we can confidently account for based on our ping interval. This ensures that even if a ping is delayed, we don't over-report active time.   
This logic allows us to incrementally and accurately compute a rider's active time, which is then sent to a separate queue for further processing and reporting.   

---

By combining an efficient ping-based presence system with a clever use of geospatial indexing and an active time calculation, we can build a highly scalable and reliable system for managing rider availability. This approach provides the necessary data for dispatching.   
   
