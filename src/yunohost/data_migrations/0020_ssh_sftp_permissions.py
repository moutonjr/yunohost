import subprocess

from moulinette import m18n
from moulinette.utils.log import getActionLogger
from moulinette.utils.filesystem import read_yaml

from yunohost.tools import Migration
from yunohost.permission import user_permission_update

logger = getActionLogger('yunohost.migration')

###################################################
# Tools used also for restoration
###################################################


class MyMigration(Migration):
    """
        Add new permissions around SSH/SFTP features
    """

    dependencies = ["extend_permissions_features"]

    @ldap_migration
    def run(self, *args):

        from yunohost.utils.ldap import _get_ldap_interface
        ldap = _get_ldap_interface()

        # Add SSH and SFTP permissions
        ldap_map = read_yaml('/usr/share/yunohost/yunohost-config/moulinette/ldap_scheme.yml')

        ldap.add("cn=ssh.main,ou=permission", ldap_map['depends_children']["cn=ssh.main,ou=permission"])
        ldap.add("cn=sftp.main,ou=permission", ldap_map['depends_children']["cn=sftp.main,ou=permission"])

        # Add a bash terminal to each users
        users = ldap.search('ou=users,dc=yunohost,dc=org', filter="(loginShell=*)", attrs=["dn", "uid", "loginShell"])
        for user in users:
            if user['loginShell'][0] == '/bin/false':
                dn=user['dn'][0].replace(',dc=yunohost,dc=org', '')
                ldap.update(dn, {'loginShell': ['/bin/bash']})
            else:
                user_permission_update("ssh.main", add=user["uid"][0], sync_perm=False)

        permission_sync_to_user()


        # Somehow this is needed otherwise the PAM thing doesn't forget about the
        # old loginShell value ?
        subprocess.call(['nscd', '-i', 'passwd'])
