---
# yaml-language-server: $schema=schemas/page.schema.json
title: "Cursor Base Pagination"
description: "Describes the steps and mental model for designing cursor base pagination with a lot of assumptions"
draft: false
date: "2025-10-30T02:13:32+01:00"
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
Creation date: "2025-10-27T18:59:18Z"
Created by:
    - ukor
Description: Describes the steps and mental model for designing cursor base pagination with a lot of assumptions
id: bafyreifioavamznrzrdp4asxg6p3uhocr7ugr2bze4rp7uyhwewhcnxjpm
---

The goal  is to document a mental note for implementing cursor-based pagination using the following payload to paginate a large set of data   
```json
{
  "before": "<sortable-id-by-time> || Optional",
  "after": "<sortable-id-by-time> || Optional",
  "limit": number,
}
```
## Sort Direction   
The majority of the time, results from the database are sorted from most recent to oldest - `descending,` assuming we are sorting by the `id` field.   
The client can also specify in what order they want the result to be sorted. For this article, I will limit sorting to descending and ascending, as enforced by the backend on the id field.   
   
Different scenarios can occur from this   
- User is making first request - `n`    
- User is making a next request - ` n + 1`     
- User is going back from - `n - 1`    
   
   
## First Request (n)   
- Request    
   
```json
{
  limit: 10,
}
```
`before` and `after` are null(falsely value) - but limit is sent or defaulted to a reasonable value if the amount sent is too large.    
The request translates to, "Get me the first 10 items that match this query".   
## Next Page (n + 1)   
- Request   
   
```json
{
  "after": 3,
  "limit": 3
}
```
For *ascending* *direction* - The request translates to,  "Return all values earlier than 3 (greater than) `3`, limit the result to 3 items"   
For *descending* *direction* - the request translates to, "Return all items older than 3 (less than), limit the result to 3 items"   
## Previous Page (n - 1)   
```json
{
  "before": 8,
  "limit": 3
}
```
For *ascending direction,* The request translates to, "Get all values older than 8 (less than), limit the result to 3   
For ascending direction, The request translates to, "Get all values inserted earlier than 8(greater than), limit the result to 3   
   
### Response Process   
```json
{
  "paginationCusor": {
    "hasNext": false,
    "hasPrevious": false,
    "after": "some-sortable-id",
    "before": "some-sortable-id",
    "limit": 10
  }
}
```
The backend **adds** 1 to the `limit`  before making a request to the database   
The database response size (cardinality) is checked against the limit in the request payload;  if the response size is greater than the `limit`, this indicates that there is more data in the database that matches the query - the `paginationCursor.hasNext` is set to `true,` and the extra item is removed from the result.   
If size is less than or equal to the limit, `hasNext` remains false.   
   
- **Ascending Direction**   
   
Given the following data and assuming our limit is set to 3   

$$
[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
$$

For the first database result  `[1, 2, 3]`    
The value of `before` is set to the last item - in this case 3 (translate to - I want item older than 3 ); id less than 3.    

$$
id < 3
$$

> ~~`before` should not be set in the first request because this is the first request, and no item is factually older than the first 3.~~   
> \
> `before` should be set for a consistent cursor.   
   
The value for `after` is set to the last item on the list - in this case, 3 (translate to - I want item earlier than 3); id is greater than 3.    

$$
id > 3
$$

`[4, 5, 6]` - before is set to 4 `(id < 4)`; after is set to 6 `(id > 6)`   

Assuming we have gone 3 request into the database, [7, 8, 9]   
before = 7; after = 9;    
If this is the first request the `hasPrevious`  field is set to false.    
To get `hasPrevious` state for `n+1`  or `n-1`  request - query the database for items less than `before`. If values are returned, `hasPrevious` is set to true and false if otherwise   
   
- **Descending Direction**   
   
Given the following data and assuming our limit is set to 3   

$$
[10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
$$

The difference between this and that of the `ascending` process is in the values of `before` and `after` in the response payload.   

The first request will return `[10,9,8]`  with after set to `8`  and before set to `10`    
When making a request for the next page(using after in the request payload), the database query will be using the less than operator; i.e get 3 items after 8 (less than 8).   

When making a back/previous request(using before in request payload), the greater than operator will be used - Assuming we have made 3 forward requests `[4,3,2]` before, will be set to 4 and after set to 2 - Going back will be "Get 3 result before 4 (greater than 4)".    

The value for the `hasPrevious` field will always be true because there is a great tendency that a new record will have been added - this assumption is entirely dependent on how frequently data is being add; feel free to modify as required.   

The value for `hasNext` can only be false if we are at the last set of item in the list [3, 2, 1]      

--- 

## Caveat

The logic stated above may differ based on the database being used.    
For MongoDB, the ObjectId is time-sortable.    
For SQL (Postgres, MySQL), I assumed that the `id` field is numeric(auto increment). I hear `UUID v7`  is time sortable, but I have not used it to validate the cursor-based pagination.   
   

