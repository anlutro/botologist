# Changelog

This document will describe **breaking changes only** and how to fix issues as you upgrade. For a full list of new features/improvements, try the commit log.

## 2015-08-22

Due to https://github.com/anlutro/ircbot/issues/11, your config will probably lead to a few error messages about plugins. To fix this:

1. Remove the "plugins" dictionary in your config.yml
2. Replace "urls" with "url" in global_plugins/channel plugins
3. Replace "redditeu_qdb" with "qdb" in global_plugins/channel plugins
4. Replace "convert" with "conversion" in global_plugins/channel plugins
