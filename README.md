# Assembl load testing

This (python3) code allows to apply [Molotov](https://github.com/loads/molotov/) load testing to arbitrary [HAR](https://en.wikipedia.org/wiki/.har) files. Those can be created easily with the command "Save as HAR with Content", in the network view of Chrome DevTools. The resulting HAR is quite large, and the `clean_har.py` utility allows to remove the content and trim the HAR file before including in this repository.

It is possible to use this either in command-line:

```bash
assembl_load_testing.py [-h] [-u USERNAME] [-p PASSWORD] [-s SERVER] configuration [har [har ...]]
```

The configuration file would contain the main arguments:

```ini
[molotov]
user=some_user
password=some_password_do_not_put_in_git
har_files = some_user_operation.har some_other_user_operation.har
server = http://some_server.example.com
```

but the CLI arguments override those; this allows easy testing of new har files. For load testing, only the configuration file will be used, as follows:

```bash
molotov assembl_load_testing.py ... 
```

with the normal [molotov command line arguments](https://molotov.readthedocs.io/en/stable/cli/).
