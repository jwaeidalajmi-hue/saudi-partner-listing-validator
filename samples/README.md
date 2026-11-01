# Samples

`../web/samples.json` holds four sample listings, one per provider type, in Arabic and English. They are the examples from the brief:

| Provider type | Listing | What the check should catch with the mock photos |
|---|---|---|
| Activities | Red Sea snorkelling trip with a pool and lunch | the coffee-cup photo is unrelated; the pool and lunch have no photo (suggestions) |
| Accommodation | AlUla lodge: bedroom with a king bed, private bathroom, pool, gym | no bathroom photo (blocks); `view.jpg` is 960×640, below HD |
| Food & Beverages | Fresh salad café | the steak photo contradicts "fresh salads" |
| Shopping | Printed t-shirt store | the coffee-cup photo is unrelated |

`mock-photos/` contains **placeholder textures**, not real photos. In mock mode the app reads each file's name to guess what it shows. Their sizes vary on purpose, so the resolution checks have something to find.

To try the real check, set `ANTHROPIC_API_KEY` and use your own photos. The repository ships no real photos because of copyright and privacy.
