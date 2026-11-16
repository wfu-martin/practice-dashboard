# Vinyl Vault Practice Dashboard: Prompts for Each Stage

> **Where to read this guide.** This guide lives on the latest version of the project (the `main` branch) and is meant to be read on the repository's page in your browser: https://github.com/wfu-martin/practice-dashboard. The older snapshots (`stage-1-spec` and so on) do not contain it, so when you switch to one of them, this file will not be in your folder. Keep this page open in your browser while you work.

## How to use this page

1. Open Claude Code in a **new, empty folder** on your computer.
2. Paste the prompts below **one at a time**, in order, pressing Enter after each. Each gray box has a copy button at its top right corner.
3. Read Claude's answer before moving to the next prompt. Each prompt shows you the project as it looked at one stage of the work. At the stages where something can run, it helps you run it and see it for yourself.

## What you need before you start

- The project lives on GitHub (public, no account needed): https://github.com/wfu-martin/practice-dashboard
- Python 3.12, or conda (Claude can tell you which you have and set up the rest). You need these only for the "run it" prompts.
- For Stage 5 only: the database login your instructor gave you. You will type the password into a file yourself. **Never paste it into the chat.**

You do not need a GitHub account. The repository is public.

## Step 0: Get the project (once)

Paste this:

```
Clone https://github.com/wfu-martin/practice-dashboard.git into the current folder, then open the project folder it creates. List the files and folders and tell me in plain language what each one is for. Tell me the full path of the project folder.
```

The clone creates a subfolder named `practice-dashboard`. Close Claude Code and reopen it **inside that new folder**, because every later prompt that says "the project folder" must run there.

## Step 0B: Set up to run the apps (once)

Paste this:

```
In the project folder, set up a Python 3.12 environment for this project (use conda if I have it, otherwise a virtual environment) and install the packages listed in requirements.txt. If Python 3.12 is not installed, tell me how to install it before you continue. Do not run any app yet. At the end, tell me the exact command I use to switch into this environment each time I come back to work.
```

## Stage 1: The spec (snapshot: stage-1-spec)

Paste this:

```
Switch to the version tagged stage-1-spec. Show me the files. Then read spec.md and tell me, in plain business language: who the dashboard is for, what decision it helps them make, and the questions it must answer.
```

Nothing to run at this stage: there are no dashboard screens yet, only the written plan. That is the point: the spec comes first.

## Stage 2: The design (snapshot: stage-2-design)

Paste this:

```
Switch to the version tagged stage-2-design. What was added since stage-1-spec? Read design.md and explain how each of the four screens answers a question from the spec, and what the style rules are for.
```

Now see the design come to life. Paste this:

```
Run the clickable mockup with: streamlit run mockup.py
Tell me the localhost web address to open in my browser (usually http://localhost:8501). Then walk me through the four screens and explain how each one matches the drawing in design.md. Remind me that the numbers in the mockup are made up.
```

The mockup needs no database login. When you are done looking, press Ctrl+C in the terminal to stop it (or paste: "Stop the app that is running.").

## Stage 3: The roadmap (snapshot: stage-3-roadmap)

First stop any app that is still running. Then paste this:

```
Switch to the version tagged stage-3-roadmap. What was added since stage-2-design? Read ROADMAP.md and explain the phases and the order of the work. Each task is a numbered GitHub Issue: explain how the tasks are grouped into phases and which ones must be finished first.
```

There is no stage 4 snapshot: the guide goes from Stage 3 to Stage 5.

Nothing new to run at this stage: the screens still look like the mockup. You can run the mockup again if you want to compare:

```
Run the clickable mockup again with: streamlit run mockup.py
and tell me the localhost address to open in my browser.
```

Tip: open the project's Issues page in your browser to see the tasks the roadmap describes: https://github.com/wfu-martin/practice-dashboard/issues

## Stage 5: The finished build (snapshot: stage-5-build-next)

First stop any app that is still running. Then paste this:

```
Switch to the version tagged stage-5-build-next. List what was added since stage-3-roadmap: new folders and files, grouped as data code, screens, and tests. Keep it short and use plain language.
```

To run the real dashboard, it needs the course database. Paste this:

```
Copy .streamlit/secrets.toml.example to .streamlit/secrets.toml, then open the new file in my default text editor so I can edit it (the .streamlit folder is hidden). Tell me which values I need to fill in. Do NOT ask me for my password here: I will type it into the file myself.
```

Type your database login values into the file and save it. The file stays on your computer only; it is never shared. Then paste this:

```
Run the dashboard with: streamlit run streamlit_app.py
Tell me the localhost web address to open in my browser (usually http://localhost:8501). Walk me through each of the four screens: what question does it answer, and what number or chart answers it? Then open the "Check against Finance" section at the bottom of a screen and explain what it proves.
```

If the app shows a database error, paste this:

```
The dashboard shows a database error. Check the field names in my .streamlit/secrets.toml (do not show me or repeat the password) and tell me what might be wrong.
```

Now see how the numbers are proven right. Paste this:

```
Open one test in the tests folder, for example tests/test_metrics_total.py, and explain in plain language how it proves that the grand total on the screen is right. Why does the test compare the number to a second, independent calculation? Then run all the tests with pytest and explain the result.
```

Finally, compare the two things you have seen. Paste this:

```
Compare the clickable mockup I ran at stage 2 with the finished dashboard I just ran. What looks the same, what changed, and what do the finished screens do that the mockup could not?
```

## Compare any two stages

First stop any app that is still running. Then paste this (change the two names to the stages you want):

```
Show me what changed between stage-2-design and stage-3-roadmap, file by file, and summarize the changes in plain language.
```

## Come back to the latest version

First stop any app that is still running. Then paste this:

```
Switch back to the latest version of the project (the main branch).
```

## Notes

- Snapshot names currently available: `stage-1-spec`, `stage-2-design`, `stage-3-roadmap`, `stage-5-build-next`. If your instructor gives you different names, use those.
- These steps work the same on Windows and Mac.
- If you see an "address already in use" message, an earlier app is still running. Press Ctrl+C in its terminal, or paste: "Stop the app that is running."
- Stop an app before you switch to another stage: press Ctrl+C in the terminal where it is running.
- Your `.streamlit/secrets.toml` stays in place when you switch stages. It is not part of any snapshot, so you only create it once.
- If Streamlit asks for your email the first time it starts, just press Enter to skip it.
- When you switch to a snapshot, Git prints a long warning about a "detached HEAD". That is normal and harmless. It only means you are looking at an old snapshot and not the latest work.
- Each snapshot is also a "release". Browse them here: https://github.com/wfu-martin/practice-dashboard/releases
- If you are told a new snapshot has been published, paste this first:

  ```
  Fetch the latest tags for this project, then list all of them.
  ```

- No Git? On the Releases page above, each snapshot has a "Source code (zip)" download. Unzip it, open that folder in Claude Code, and use the same "run it" prompts above.
