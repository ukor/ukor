---
# yaml-language-server: $schema=schemas/page.schema.json
title: "Migrating from CommonJs to ESM"
description: "Describes the reason and pain point while migrating from CommonJs to EcmaScript"
draft: false
date: "2026-03-13T14:02:27+01:00"
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
Creation date: "2025-10-27T18:59:18Z"
Created by:
    - ukor
Description: "Describes the reason and pain point while migrating from CommonJs to EcmaScript"
id: bafyreicuhjsaiyd7v6q5t56zzvyxp422hrpnpw2capduvjyjps4xol7cgy
---

I ran into an issue this week in a codebase that I have been an active contributor to for over 4 years. The codebase started as a monolithic application that was bootstrapped with CommonJS; ever since then, it has gone through several changes.   
   
From a monolithic application to a micro-service application managed with TurboRepo, and now a micro-service application managed by just `PNPM`  workspace. Why we switched from TurboRepo to `PNPM` workspace is a story for another day.   
   
Today, I want to give you the backstory of how we hit a deadlock with CommonJS and started planning our migration to ESM.   
When we started the project, we did not think much about the different module types in JavaScript; we just bootstrapped the project with the default configuration of NPM and started writing code.   

This week, we thought it was time to improve the service that was responsible for intra-service communication. All our services communicate over HTTP, and we use Axios as the HTTP client.   
My goal is to create a common interface for the intra-service communication module, to give us the flexibility of swapping the underlying HTTP client.   
   
We picked Got.  

Why `GOT`  over `Axios`? Got offers better default security, advanced retry mechanisms and HTTP2 support. Got is more lightweight and efficient for the NodeJS environment. Axios is more popular, but Got offers more value for us. We also wanted to introduce some new features to our intra-service communication module, like an alert after a number of retries to another service. We wanted to take advantage of the hooks system in Got.   
   
Back to the ESM debacle, after implementing our communication service in Got, we could not use it with our codebase as GOT is a fully ESM module.

This realisation was what led me to start researching the ESM module. Oooh, the benefits that come with ESM. 

Why did I not know this when we started this project?    
   
I went further  to read about migrating from CommonJS to ESM; now this is where the real pain of migration started dawning on me.   
   
ESM is the future, so it is either now or postpone the pain to the future. I decided it's best to go through the pain now because the more we push it to the future, the more the codebase grows.    
So, I proposed to the team why we should start migrating, and I also offered a plan for migration.    
Incremental changes, one service at a time - We start from the services with less code and move up. Our internal shared package will be the last thing to change since ESM modules are backwards compatible with CommonJS
   
After assessing what needs to change on the codebase. We decided to try it on the service with the smallest code - let's call this service `project\_small`    
   
Project\_small is responsible for handling all webhook requests. It handles webhook request validate that they are coming from the right provider then sends the payload to the appropriate service via a message queue.   
## The Pain Points   
Here are some of the migration pain point from `project\_small`    
First, we need to add the `"type"` field to the package.json file for project\_small. The value for this was `module`. This was the simplest part.   
Adding the type field with a value of `module`  tells NodeJs to treat this project as ESM module, so we don't need to rename files extensions to `.mts` - which is a more painful approach.   
### Importing with file extension   
ESM requires that you import JavaScript files with their extension.   
I can no longer do this   
```Typescript
import { hello } from '../world';


```
rather, I have to do this   
```Typescript
import { hello } from '../world.js';
```
Doing this for a few files is fine, but for a 4-year project with multiple files and some dead code. Pain! - Pain and boredom are all I see.   
Another thing that made this painful, is that in commonJS you can import a folder and the NodeJS will default it to the index file in that folder but ESM enforce that a file must be reference.   
It took me a while to wrap my head around importing a JavaScript file in a TypeScript file, but after some reading, I understand why that is. Matt Pocock's [article](https://www.totaltypescript.com/relative-import-paths-need-explicit-file-extensions-in-ecmascript-imports) and video helped me understand the reason.   
It simplifies Node's module resolution strategy - Node doesn't have to do any guesswork to figure out what file to import   
I thought about writing a script in Python that scans through our codebase and prefixes `.js` to all import that looks like a relative path.    
This was going to take some time to plan and implement, and would be overkill for a small code base like that of `project\_small`.    
### Importing Built-in libraries   
Importing built-in libraries also needs changes, for example, I changed this   
```Typescript
import path from 'path';

```
to this   
```Typescript
import path from 'node:path';

```
This was just to avoid name collision; amd for security purpose. The Official NodeJS module documentation highlight this.   
### Global Constants   
Another pain point was that in ESM  the "__dirname" and "__filename" globals does not exist   
I had to learn about    
```Typescript
"import.meta.url"
```
   
At the end I abstracted the code below to a utils file   
```Typescript
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
```
   
The next pain point was with third party library what ends with `.js`, a good example of such was `currency.js.` During execution, everything works fine, but during testing, it becomes a pain point. I have not found a solution for this, and I will talk more about it in the test session   
   
The final pain point was testing; we used Jest for testing. I remember when we first added Jest to the codebase; it was a painful process. Migrating to ESM reminded me how painful that process was. Determined not to go through it again, we switched to Vitest. Secondly, our Jest configuration did not work out of the box with ESM, as it was finding it hard to resolve the `.js`  import   
One thing that took me a while to wrap my head around is that our tests are written in Typescript, but when we import files from the source( `src`  ) directory, we have to prefix each file with `.js`    
It felt awkward importing a JavaScript file in a TypeScript file, and also, the file I was importing is in TypeScript. I read somewhere that Vitest is smart enough to resolve this, but how? Magic!    

> Vitest creates a **module graph**. When it encounters `import ... from './file.js'`, the alias interceptor kicks in, changes the request to `./file.ts`, and then the `vite` pipeline uses `esbuild` to compile that TS file on-the-fly into memory.   

Vitest did not need any configuration to setup, but after going through the documentation we added a few configuration for a project setup on the root folder and also added another configuration in the root of `project\_small`    
The root configuration, point Vitest to the each services by referencing the vitest configuration in each service.    
```
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    projects: [
      'apps/*/vitest.config.ts',
    ]
}
})
```
For each service in the `apps` directory I added a more detailed configuration. Everything works as expected except for the file that uses the currency.js library. This was another pain point, after a couple of reading and chat with Google Gemini, this configuration resolved it for me   
```Typescript
import { defineConfig } from 'vitest/config';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);

export default defineConfig({
	test: {
		globals: true, // Allows using 'describe', 'it', 'expect' without importing them
		environment: 'node',
		include: ['**/__test__/**/*.spec.ts'],
		coverage: {
			reporter: ['text', 'json', 'html'],
		},
		deps: {
			optimizer: {
				web: {
					include: ['currency.js']
				},
				ssr: {
					include: ['currency.js']
				}
			}
		},

	},
	optimizeDeps: {
		include: ['currency.js'],
	},
	ssr: {
    noExternal: ['currency.js'],
  },
	resolve: {
		alias: [
			{
				/**
         * ^(\.?\.\/.*)\.js$
         * This strictly matches paths starting with ./ or ../
         * It prevents 'currency.js' (a package) from being
         * caught and renamed to 'currency.ts' (which doesn't exist).
         */
        find: /^(\.?\.\/.*)\.js$/,
				replacement: '$1.ts',
			},
			{
				find: 'currency.js',
				replacement: require.resolve('currency.js'),
			},
		],
		extensions: ['.ts', '.js', '.mts'],
	},
});
```
   
### ESM and PM2 Configuration   
Migrating to ESM also change our PM@ configuration. The changes were in the `cwd`  field and `node\_args`    
   
```Typescript
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));


export default {
  apps: [
  {
			name: 'project_small_prd',
			script: './build/index.js',
			cwd: __dirname,
			instances: 'max',
			exec_mode: 'cluster',
			autorestart: true,
			watch: false,
			ignore_watch: ['node_modules'],
			max_memory_restart: '1G',
			output: '~/.pm2/logs/out.log',
			error: '~/.pm2/logs/error.log',
			merge_logs: true,
			log_date_format: 'YYYY/MM/DD h:mm:ss A',
			kill_timeout: 3000,
			wait_ready: true,
			max_restarts: 5,
			min_uptime: 2000,
			listen_timeout: 10000,
			exp_backoff_restart_delay: 100, // 100ms
			restart_delay: 5000, // wait for five seconds before restarting
			source_map_support: true,

			node_args: [
				'—trace-warnings',
				'—enable-source-maps',
				'—import',
				path.resolve(__dirname, './instrumentation.js'),
			],
		},
  ]

}
```
   
 --- 
## Automating prefixing .js extension   
I found out about `jscodeshift`, a toolkit from Meta that automates syntax transformation. I am yet to use it, but I will provide more details when I do.   
   
 --- 
## Reference   
- [Modules Official Node Documentation ](https://nodejs.org/api/modules.html)    
- [Relative import paths need explicit file extensions in EcmaScript imports](https://www.totaltypescript.com/relative-import-paths-need-explicit-file-extensions-in-ecmascript-imports)    
- [Twitter conversation between Matt and Gil Tayer](https://x.com/giltayar/status/1711670026464354460)    
   
---

This article was also publish on my [LinkedIn Page](https://www.linkedin.com/pulse/migrating-from-commonjs-esm-jidechi-ukor-60d7f/?trackingId=R9yq48kZQ5yHtUb34jTikQ%3D%3D)
  

