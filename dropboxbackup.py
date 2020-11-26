from lib import (to_remove_closer_elements, FolderHandler, DropboxHandler, get_password)
import argparse
import logging
#logging.basicConfig(level=logging.DEBUG, format='%(asctime)s -  %(levelname)s -  %(message)s')
logging.disable()

parser = argparse.ArgumentParser(description='Backup to dropbox given folder')
parser.add_argument("-n","--name",required=True, type=str, help="Folder name")
parser.add_argument("-p","--path",required=True, type=str, help="Local path")
parser.add_argument("-t","--token",required=True, type=str, help="Token path")
parser.add_argument("-v","--versioning", required=False, type=bool, default=False, help='Keep versions of file')

password_group = parser.add_mutually_exclusive_group()
password_group.add_argument("-pw","--password", default = None, type=str, help="Password for the zip file")
password_group.add_argument("-pwp","--password_path", default = None, type=str, help="File containing the password")
args = parser.parse_args()

# First I should define the password I want to use:
password = get_password(args.password_path,args.password)
db_handler = DropboxHandler(args.token)

folder = FolderHandler(args.name,args.path,db_handler,password)
folder.make_archive()

if args.versioning:
    db_handler.delete_older_backups('/' + args.name)
    folder.upload_file(db_handler)
else:
    db_handler.backup_old_backup('/' + args.name)
    folder.upload_file(db_handler, single_file=True)
folder.remove_archive()