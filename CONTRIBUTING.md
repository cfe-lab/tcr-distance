This is a Django app deployed on the server with some other Django apps.

## Deploying a Release
You need to connect to the server from inside the lab network. You can find the
internal IP address in the `servers.md` file in the `dev-docs` repository. If
you don't already have an account on the server, ask the lab director for
access.

The source code is deployed with a Git clone at
`/alldata/bblab_site/tools/tcr_distance`. To deploy an update, change to that
directory, and then run `sudo git pull`. 

Note that the contents of `static/` should go in `/alldata/bblab_site/static/`. 
This includes `tcr_dist_style.css` and `tcr_dist.js`.

Then restart the Apache server with
`sudo systemctl restart httpd`

## Note: tcr-dist
This tools uses [`tcr-dist`]. This repo is tracked on the server in
`/alldata/bblab_site/depend/apps/tcr_dist/`. This project seems fairly stable
as of early 2022, but make sure to monitor this tool and keep up to date.


[`tcr-dist`]: https://github.com/phbradley/tcr-dist