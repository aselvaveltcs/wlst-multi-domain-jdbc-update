# wlst-multi-domain-jdbc-update
This repository provides a WebLogic's WLST script that can be used
to update JDBC urls for multiple datasources defined on multiple domains.

## Config
The diferent domains must be defined in a textfile with the following format:

    DESCRIPTION cluster_name t3_admin_hostname:t3_admin_port adm_user adm_password
It multiple lines are found, the change will be applied by connecting to the admin as described on each line .

The new URLs must be defined in a text file with the following format:

    SERVICE_NAME:
        hostname1:port
        hostname2:port

