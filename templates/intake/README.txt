FILL-IN SPREADSHEETS — Writing System Intake
=============================================

These four CSV files let you build your whole cast, world, groups, and chapter
list in a spreadsheet instead of typing them one at a time.

  characters.csv   your cast
  locations.csv    your places
  groups.csv       your factions / guilds / families / crews
  chapters.csv     your book's chapter list

HOW TO USE
----------
1. Open any of these files in a spreadsheet program:
     - Google Sheets:  File > Import > Upload, pick the CSV, "Replace spreadsheet".
     - Excel / LibreOffice:  just double-click the file.
2. Each file has a header row (the columns) and ONE example row showing how to fill
   it in. The example row starts with "[EXAMPLE]" — delete it before importing.
3. Add your own rows. You only have to fill the first column or two; everything
   else is optional and can be left blank to write later in the web editors.
4. Save / export back to CSV (in Google Sheets: File > Download > Comma-separated
   values). Keep the same file name.
5. In Claude Code, run:  /novel-import
   It reads the filled CSVs, builds the rows, and links everything for you.

WHAT YOU DON'T HAVE TO WORRY ABOUT
----------------------------------
- IDs and keys: you never type one. You give names; the system generates the
  internal ids and connects the tables.
- Links: write a leader or POV character by NAME (e.g. "Lady Vex"). The import
  matches it to the character you created. If you name someone who isn't in
  characters.csv yet, the import will tell you — add them first.
- Order: import characters and locations first, then groups (which reference a
  leader) and chapters (which reference a POV character and a location).

COLUMN NOTES
------------
characters.csv  name is required (it's the only thing you must give). role is one of:
                protagonist, antagonist, ally, minor, narrator. (There is no "minor
                age" field — by design.)
locations.csv   display_name is required. type is free text (interior, exterior,
                district, landmark, region, ...).
groups.csv      display_name is required. leader must match a character name exactly,
                or leave it blank.
chapters.csv    book, chapter, part are the keys — book name plus a number (part is
                usually 1). pov_char = a character name; location = a location's
                display name. status defaults to "concept", priority to "MED".

PREFER TO JUST TALK?
--------------------
You don't need these files at all. You can instead run /novel-add-characters,
/novel-add-locations, /novel-add-group, or /novel-add-book in Claude Code and give
the list in plain conversation. The spreadsheets are just for bulk entry.
