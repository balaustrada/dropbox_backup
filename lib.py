import dropbox as db
import os
import sys
import shutil #for moving folders, create zip
from datetime import datetime
import zipfile
import subprocess

################################################
############                        ############
############    FUNCTIONS SECTION   ############
############                        ############
################################################
def get_password(password_path,password):
    if password_path:
        with open(password_path,'r') as file:
            return file.read().replace('\n', '')
    else:
        return password

def to_remove_closer_elements(time_list, distance):
    to_remove = []
    # Last unremoved element is the first one
    last_unremoved = time_list[0]
    for i in range(len(time_list)-1):
        # If the distance from the last unremoved to the next is smaller than the required, 
        # I append the element to the remove list and of course it won't count as last unremoved
        if ( last_unremoved - time_list[i+1] ).total_seconds() < distance:
            to_remove.append(time_list[i+1])
        else:
            last_unremoved = time_list[i+1]
    return to_remove

class FolderHandler:
    def __init__(self,name,path,db_handler,password):
        self.__name__ = name
        self.path = path
        self.password = password
        
    def make_archive(self):
        self.archive_path = self.__name__ + '.zip'
        if self.password:
            rc = subprocess.call(['7z', 'a', '-mem=AES256', '-p'+self.password, '-y', self.archive_path] + 
                     [self.path])
        else:
            shutil.make_archive(self.__name__,'zip',self.path)

    def upload_file(self,db_handler, single_file=False):
        now = datetime.now()
        dbx = db_handler.dbx
        file_path = self.archive_path
        
        if single_file:
            destination_path = '/' + self.__name__
        else:
            destination_path = '/' + self.__name__ + '/'+now.strftime("version-%Y-%m-%d-%H-%M-%S.zip")
        
        f = open(file_path, 'rb')
        file_size = os.path.getsize(file_path)

        CHUNK_SIZE = 4 * 1024 * 1024

        if file_size <= CHUNK_SIZE:

            dbx.files_upload(f.read(), destination_path)

        else:

            upload_session_start_result = dbx.files_upload_session_start(f.read(CHUNK_SIZE))
            cursor = db.files.UploadSessionCursor(session_id=upload_session_start_result.session_id,
                                                       offset=f.tell())
            commit = db.files.CommitInfo(path=destination_path)

            while f.tell() < file_size:
                if ((file_size - f.tell()) <= CHUNK_SIZE):
                    dbx.files_upload_session_finish(f.read(CHUNK_SIZE),
                                                    cursor,
                                                    commit)
                else:
                    dbx.files_upload_session_append(f.read(CHUNK_SIZE),
                                                    cursor.session_id,
                                                    cursor.offset)
                    cursor.offset = f.tell()

        f.close()
        return
    
    def remove_archive(self):
        os.remove(self.archive_path)

class DropboxHandler:
    def __init__(self,token):
        with open(token,'r') as file:
            token = file.read().replace('\n', '')
        self.dbx = db.Dropbox(token)

    def file_exists(self, path):
        try:
            self.dbx.files_get_metadata(path)
            return True
        except:
            return False

    def backup_old_backup(self, path):
        if self.file_exists(path + '_old.zip'):
            self.dbx.files_delete(path + '_old.zip')
        
        if self.file_exists(path):
            _ = self.dbx.files_move(from_path=path, to_path=path + '_old.zip')

    def delete_older_backups(self,path):
        try:
            self.dbx.files_create_folder(path)
        except:
            now = datetime.now()

            # We get the entries datetimes and path_display, the first is for ordering, the second is for removing if needed.
            entries = {}
            for entry in self.dbx.files_list_folder(path).entries:
                entries[entry.server_modified] = entry.path_display

            last_week = sorted( list( filter(lambda x: (now-x).days <= 7, entries.keys())) , reverse = True)
            last_week_to_month = sorted( list( filter(lambda x: (now-x).days > 7 and (now-x).days <= 31, entries.keys())) , reverse = True) 
            month_to_three_months = sorted( list( filter(lambda x: (now-x).days >31 and (now-x).days < 93, entries.keys())), reverse = True)

            remove_times = []
            if len(last_week) > 30:
                remove_times.extend( to_remove_closer_elements(last_week, 3600*0.5) )

            if len(last_week_to_month) > 40:
                remove_times.extend( to_remove_closer_elements(last_week_to_month, 3600*15) )

            if len(month_to_three_months) > 5:
                remove_times.extend( to_remove_closer_elements(month_to_three_months, 3600*24*15) )

            for x in set(remove_times):        
                self.dbx.files_delete(entries[x])
            
    
