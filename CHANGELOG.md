# Changelog

This document will describe **breaking changes only** and how to fix issues as you upgrade. For a full list of new features/improvements, try the commit log.

## 2015-08-29

Renamed the entire module from "ircbot" to "botologist".

## 2015-08-22

### Plugin system refactored

Due to [#11](https://github.com/anlutro/botologist/issues/11), your config will probably lead to a few error messages about plugins. To fix this:

1. Remove the "plugins" map in your config.yml
2. Replace "urls" with "url" in global_plugins/channel plugins
3. Replace "redditeu_qdb" with "qdb" in global_plugins/channel plugins
4. Replace "convert" with "conversion" in global_plugins/channel plugins

### Config restructuring

Remove the line "bot:" from your config.yml, and un-indent everything that was inside that map.
