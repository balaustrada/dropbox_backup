# dropbox_backup
Python code to handle backups using the DROPBOX api. 

The usage is very simple:
- -t defines the token from Dropbox needed to acces the Dropbox contnet.
- -p defines the path to be backuped
- -n defines the name of the folder where the backup will be stored (inside Dropbox). 

The program handles the backups included in the same folder as the new one. This behaviour is driven by the function DropboxHandler.delete_older_backups. It will be good to change it in the future for something better, but it works. 
