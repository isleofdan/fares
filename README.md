# fares

A personal system that tracks business and first class round-trip airfares from Tokyo on four routes (Houston, Detroit, Tel Aviv, Barcelona).
Once a day it quietly records the prices it finds into a price history on Dan's machine, and nothing is ever overwritten.
A second program turns that history into one plain web page showing today's prices against each route's own past prices.
The aim is to spot real deals and to learn how airfares behave; `LEARNING.md` collects what the data teaches.
Route rules live in `routes.json`; current state and decisions are in `PLAN.md`.
