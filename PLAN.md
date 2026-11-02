# Plan

## Current state

Step 7.1 (skeleton) done: README, this plan, an empty LEARNING.md, the route profiles in `routes.json`, and a `.gitignore`.

## Decisions

- Persistent place for the store, the page, the logs and the loop log: `/data/home/dan/fares-data/` (outside the repository; per FACTS.md anything that must survive a deploy lives under `/data/home/dan`).
- Python standard library and SQLite by preference. Any third-party package is declared in the repository and installed into a virtualenv in the clone or under `/data/home/dan/fares-data`, never system-wide.
- No keys, accounts or signed-in browsers this session.
- Route rules live in one data file, `routes.json`.

## Fare sources tried

(step 7.2)

## Close-out notes

(none yet)
