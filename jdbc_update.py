"""
   Copyright 2018, João Pinto

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

    For details on how to use this script check the README.md
"""

from datetime import datetime
import re

JDBC_URL_TEMPLATE = """
jdbc:oracle:thin:@(DESCRIPTION=
                    (ADDRESS_LIST=(LOAD_BALANCE=OFF)(FAILOVER=ON)
%s
                    )
                    (CONNECT_DATA=(SERVER=DEDICATED)(SERVICE_NAME=%s))
                )
"""
JDBC_ADDRESS_LINE = "\t\t\t(ADDRESS=(PROTOCOL=TCP)(HOST=%s)(PORT=%s))\n"


class JDBC_Mapper:

    def __init__(self, filename):
        self._service_map = {}
        service_name = ''
        data = open(filename).read().splitlines()
        data.append("X")  # force flush at the last element
        connection_list_str = ""
        for line in data:
            if line[0] == "#":
                continue
            if line[0] in [" ", "t"]:
                hostname, port = line.strip().split(':')
                connection_list_str += JDBC_ADDRESS_LINE % (hostname, port)
            else:
                if connection_list_str:
                    new_url = JDBC_URL_TEMPLATE % (connection_list_str, service_name)
                    for strip_char in " \n\t":
                        new_url = new_url.replace(strip_char,'')
                    self._service_map[service_name] = new_url
                    connection_list_str = ""
                service_name = line

    def get_url(self, name):
        for key, value in self._service_map.iteritems():
            if key.lower() == name.lower():
                return value
        return None

def oracle_sn(url):
    """ Return the Oracle Service Name from a JDBC url """
    sn_match = re.findall('SERVICE_NAME=([^)]+)', url)
    if len(sn_match) == 1:
        return sn_match[0]
    if not '/' in url:
        return url
    return url.split('/')[-1]

def targets_jarray(targets_string):
    """
    Transforms the jarray representation string into a jarray

    Arguments:
    targets_string -- the targets string

    Returns:
    A jarray with the targets
    """
    objects = []
    target_list = eval(targets_string)
    for target in target_list:
        splited_list = target.split('.')
        if len(splited_list) > 2:
            ttype = splited_list.pop()
            tname = '.'.join(splited_list)
        else:
            tname, ttype = splited_list

        objects.append(get_mbean(tname, ttype))

    t_jarray = jarray.array(objects, weblogic.management.configuration.TargetMBean)
    return t_jarray

def get_mbean(_name, _type):
    """
    Returns a mbean by the given path
    """
    path = '/%ss/%s' % (_type, _name)
    return getMBean(path)

def change_url(datasource, new_url):
    url = datasource.JDBCResource.JDBCDriverParams.url

    print "CHANGE [%s] \n\t%s\n->\n\t%s\n" % (datasource.name, url, new_url)
    datasource.JDBCResource.JDBCDriverParams.url = new_url
    datasource.setTargets(targets_jarray('[]'))


def update_matching_datasources(func, url_match=None):
    """
    loop all datasources executin func() for those with url matching url_match
    return list of ds names that matched the url, or are in the selected names
    """
    jdbc_mapper = JDBC_Mapper(sys.argv[2])
    matched = []

    datasourceList = cmo.getJDBCSystemResources()
    for ds in datasourceList:
        driverName = ds.JDBCResource.JDBCDriverParams.driverName
        if not driverName:
            continue
        url = ds.JDBCResource.JDBCDriverParams.url
        if url_match and not url.startswith(url_match):
            print "Skipping", url
            continue
        service_name = oracle_sn(url)
        new_url = jdbc_mapper.get_url(service_name)
        if new_url:
            matched.append(ds.name)
            change_url(ds, new_url)
        else:
            print "KEEP [%s] [%s]" % (ds.name, url)
    return matched

def main():
    redirect('/dev/null', 'false')
    domain_list = open(sys.argv[1]).read().splitlines()

    print "\n" + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for domain in domain_list:
        block, cluster, admin_url, username, password = domain.split()
        changed_ds = []
        print "\nConnecting to " + admin_url + "...",
        connect(username, password, admin_url)
        edit()
        startEdit()
        affected_datasources = update_matching_datasources(change_url, "jdbc:oracle")
        activate()
        edit()
        startEdit()
        for ds_name in affected_datasources:
            jdbc_datasource = cmo.lookupJDBCSystemResource(ds_name)
            print "Retargeting %s" % ds_name
            jdbc_datasource.setTargets(targets_jarray("['" + cluster + ".Cluster']"))
        save()
        activate()
        disconnect()



if __name__ == "main":   # wslt invokation
    main()
