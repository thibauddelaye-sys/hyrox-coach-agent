# Knowledge base sources

The Hyrox Coach RAG layer is grounded in the following five sources. All are used in extract or open-access form. Add new sources here before running `rag-ingestion/ingest.py`.

| # | Title | Author / Publisher | Type | Format | URL / source | Date accessed | Notes |
|---|---|---|---|---|---|---|---|
| 1 | Hyrox Training Guide 2025 | Hyrox (official) | Guide | PDF | hyrox.com/training | YYYY-MM-DD | Source primary for race format, station techniques, and intensity zones |
| 2 | Periodization principles | Joe Friel (from *The Triathlete's Training Bible*, extracts) | Book extract | Markdown | TBD — extract the chapters on base/build/peak/taper | YYYY-MM-DD | Used in *extract* form only |
| 3 | ISSN Position Stand: Nutrient Timing | International Society of Sports Nutrition | Academic paper | PDF | open-access — jissn.biomedcentral.com | YYYY-MM-DD | Citable scientific basis for fuelling strategy |
| 4 | Sport Nutrition articles | Asker Jeukendrup | Web articles | Markdown | mysportscience.com (selected articles) | YYYY-MM-DD | World reference on carbohydrate strategy during training |
| 5 | First-Hyrox prep notes | Various community authors | Web articles | Markdown | 2-3 well-regarded blog posts (e.g. Hyrox forum) | YYYY-MM-DD | Practical first-timer advice |

## Adding a source

1. Place the file in this directory under a slug-cased filename: e.g. `02-joe-friel-periodization.md`
2. Add a row to the table above with title, author, type, URL, and date
3. Verify the source is freely usable in extract form (not full redistribution of copyrighted books)
4. Re-run `python rag-ingestion/ingest.py`
5. Test that the new content is retrievable with `python rag-ingestion/retrieve.py` on a relevant query
