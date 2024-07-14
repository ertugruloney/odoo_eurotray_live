# curl -X POST -F 'master_pwd=abcd' -F 'name=xyz' -F 'backup_format=zip' -o /path/xyz.zip http://localhost:8069/web/database/backup
import requests
import argparse
import os
import datetime
import psycopg2
import paramiko
import subprocess
from urllib.parse import urlparse
# from lxml.html import fromstring
import json

def init_parser():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--mpswd', action='store',
                        help='Master password Odoo')
    parser.add_argument('--url', action='store',
                        help='saas client url')
    parser.add_argument('--dbname', action='store',
                        help='name of database to backup')
    parser.add_argument('--maindb', action='store',
                        help='name of main database')
    parser.add_argument('--dbuser', action='store',
                        help='username of main database')
    parser.add_argument('--dbpassword', action='store',
                        help='password of main database')
    parser.add_argument('--processid', action='store',
                        help='process id')
    parser.add_argument('--bkploc', action='store',
                        help='backup location local, dedicated, s3')
    parser.add_argument('--path', action='store',
                        help='Backup Path')
    parser.add_argument('--backup_format', action='store',
                        help='Backup Type')
    
    parser.add_argument('--rhost', action='store',
                help='Remote Hostname')
    parser.add_argument('--rport', action='store',
                help='Remote Port')
    parser.add_argument('--ruser', action='store',
                help='Remote User')
    parser.add_argument('--rpass', action='store',
                help='Remote Password')
    
    parser.add_argument('--temp_bkp_path', action='store',
                help='Temporary Backup Directory')

    return parser.parse_args()


def database_entry(main_db, db_user, db_password, db_name, file_name, process_id, file_path, url, backup_date_time, status, message):
    try:
        if db_user == "False" or db_password == "False":
            connection = psycopg2.connect(database=main_db)
        else:
            connection = psycopg2.connect(user=db_user, password=db_password, host="127.0.0.1", port="5432", database=main_db)
    except Exception as e:
        print(e)
        print('Exited')
        exit(0)

    try:
        file_path = file_path.replace('//', '/')
        url = url.replace('//', '/')
        # Connect to database
        QUERY = "INSERT INTO backup_process_detail (name, file_name, backup_process_id, file_path, url, backup_date_time, status, message) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"
        RECORD = (db_name, file_name, process_id, file_path, url, backup_date_time, status, message)
        cursor = connection.cursor()
        print("PostgreSQL server information")
        print(connection.get_dsn_parameters(), "\n")
        cursor.execute(QUERY, RECORD)
        connection.commit()
        count = cursor.rowcount
        print(count, "Record inserted")
    except Exception as e:
        print(e)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Postgresql Connection Closed")



def login_remote(args):
    try:
        ssh_obj = paramiko.SSHClient()
        ssh_obj.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_obj.connect(hostname=args.rhost, username=args.ruser, password=args.rpass,port=args.rport)
        return ssh_obj
    except Exception as e:
        print("Couldn't connect remote")
        return False
    
def execute_on_shell(self,cmd):
    try:
        res = subprocess.check_output(cmd,stderr=subprocess.STDOUT,shell=True)
        print("-----------COMMAND RESULT--------", res)
        return True
    except Exception as e:
        print("+++++++++++++ERRROR++++",e)
        return False

def execute_on_remote_shell(ssh_obj,command):
    # _logger.info(command)
    print(command)
    response = dict()
    try:
        ssh_stdin, ssh_stdout, ssh_stderr = ssh_obj.exec_command(command)
        # _logger.info(ssh_stdout.readlines())
        print("execute_on_remote_shell out: ")
        res = ssh_stdout.readlines()
        print(res)
        print("execute_on_remote_shell err: ")
        err = ssh_stderr.readlines()
        print(err)
        if err:
            response['status'] = False
            response['message'] = err
            return response
        response['status'] = True
        response['result'] = res
        return response
    except Exception as e:
        print("+++ERROR++",command)
        print("++++++++++ERROR++++",e)
        return False




def backup_db():
    print(args)
    data = {
        'master_pwd': args.mpswd,
        'name': args.dbname,
        # 'backup_format': 'zip'
        'backup_format': args.backup_format or "zip"
    }
    
    backup_format = args.backup_format or "zip"

    client_url = ''
    msg = ''
    if urlparse(args.url).scheme not in ['http','https']:
        client_url = 'http://' + args.url + \
            ('/' if args.url[-1] != '/' else '')
    else:
        client_url = args.url + ('/' if args.url[-1] != '/' else '')

    if args.bkploc == 'remote':
        print("bkploc == remote")
        
        backup_dir = os.path.join(args.path, 'backups')
        # filename = args.dbname + '-' + datetime.datetime.now().strftime("%m-%d-%Y-%H") + '.zip'
        
        #add logic for remote server 
        try:
            ssh_obj = login_remote(args)

            print("ssh_obj",ssh_obj)
            cmd = "ls %s"%(backup_dir)
            print(cmd)
            check_path = execute_on_remote_shell(ssh_obj,cmd)
            print("check_path",check_path)
            if not check_path.get('status'):
                print("Error while checking the path of remote directory - ", check_path.get('message'))
            if not check_path.get('result'):
                cmd = "mkdir -p %s; chmod -R 777 %s"%(backup_dir, backup_dir)
                upd_permission = execute_on_remote_shell(ssh_obj,cmd)
                if not upd_permission.get('status'):
                    print("Error while creating directory and updating permissions - ", check_path.get('message'))
                    raise Exception("Cannot create remote directory and update permissions.")
        except Exception as e:
            print("Error: Creating Backup Directory")
            msg = 'Failed at ' + datetime.datetime.now().strftime("%m-%d-%Y-%H:%M:%S") + ' ' + str(e)
            #database_entry(args.maindb, args.dbuser, args.dbpassword, args.dbname, filename, args.processid, backup_dir+'/', backup_file_path, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), status="Failure", message=msg)
            return {
                'success': False,
                'msg': msg
            }

        client_url += 'saas/database/backup'
        # Without Streaming method
        print(client_url)
        # Streaming zip, so that everything is not stored in RAM.
        try:
            # filename = args.dbname + '-' + datetime.datetime.now().strftime("%m-%d-%Y-%H") + '.zip'
            backup_file_path = None
            tmp_bkp_path = args.temp_bkp_path
            print("tmp_bkp_path -", tmp_bkp_path)
            res = None
            data['backup_dir'] = tmp_bkp_path
            with requests.post(client_url, data=data, stream=True) as response:
                res = json.loads((response.content).decode())
                if not res.get('status'):
                    raise Exception(res.get('error_message'))
                
                
                # response.raise_for_status()

                #Create temporary backup file on Main Server on configured path
                
                # with open(os.path.join(tmp_bkp_path, filename), 'wb') as file:
                #     for chunk in response.iter_content(chunk_size=1024):
                #         if chunk:
                #             file.write(chunk)

                # PUT on remote server

                sftp = ssh_obj.open_sftp()
                sftp.put(tmp_bkp_path+"/"+res.get('filename'),backup_dir+'/'+res.get('filename'))
                sftp.close()
                
                
                cmd = f"ls -f {backup_dir+'/'+res.get('filename')}"
                
                # Checking if the backup file is successfully copied to remote server
                check_file_exist = execute_on_remote_shell(ssh_obj,cmd)
                if check_file_exist.get("status"):
                    print("\nBackup file successfully copied to the remote server.")
                    backup_file_path = os.path.join(backup_dir, res.get('filename'))
                    print("remote backup_file_path --->", backup_file_path)
                    
                    # DELETE the temporary backup file from the Main Server
                    if os.path.exists(tmp_bkp_path+"/"+res.get('filename')):
                        os.remove(tmp_bkp_path+"/"+res.get('filename'))
                        print("\nBackup file successfully deleted from the Main Server.")
                else:
                    print("\nBackup file doesn't successfully moved to the remote server.")
                    raise Exception("Backup file couldn't be moved to remote server.")
                


            msg = 'Database backup Successful at ' + datetime.datetime.now().strftime("%m-%d-%Y-%H:%M:%S")
            database_entry(args.maindb, args.dbuser, args.dbpassword, args.dbname, res.get('filename'), args.processid, backup_dir+'/', backup_file_path, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), status="Success", message=msg)
            return {
                'success': True,
                'msg': msg
            }
        except Exception as e:
            msg = 'Failed at ' + datetime.datetime.now().strftime("%m-%d-%Y-%H:%M:%S") + ' ' + str(e)
            database_entry(args.maindb, args.dbuser, args.dbpassword, args.dbname, res.get('filename') if res else '', args.processid, backup_dir+'/', backup_file_path if backup_file_path else '', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), status="Failure", message=msg)
            return {
                'success': False,
                'msg': msg
            }


    else:
        if not os.path.exists(args.path):
            os.makedirs(args.path)

        
        backup_dir = os.path.join(args.path, 'backups')
        if not os.path.exists(backup_dir):
            os.mkdir(backup_dir)

        client_url += 'saas/database/backup'
        print(client_url)
        try:
            # if backup_format == "zip":
            #     filename = args.dbname + '-' + datetime.datetime.now().strftime("%m-%d-%Y-%H") + '.zip'
            # else:
            #     filename = args.dbname + '-' + datetime.datetime.now().strftime("%m-%d-%Y-%H") + '.dump'
            res = None
            backup_file_path = None
            data['backup_dir'] = backup_dir
            with requests.post(client_url, data=data, stream=True) as response:
                res = json.loads((response.content).decode())
                if not res.get('status'):
                    raise Exception(res.get('error_message'))
                
                backup_file_path = os.path.join(backup_dir, res.get('filename'))
                print("local backup_file_path --->", backup_file_path)
                
                # response.raise_for_status()
                # if response.headers.get('Content-Disposition'):
                #     with open(os.path.join(backup_dir, filename), 'wb') as file:
                #         for chunk in response.iter_content(chunk_size=1024):
                #             if chunk:
                #                 file.write(chunk)
                # else:
                #     h = response.content.decode('utf-8')
                #     tree = fromstring(h)
                #     ele = tree.cssselect("div.alert-danger")
                #     if ele:
                #         err = ele[0].text_content()
                #         raise Exception(err)
            
            msg = 'Database backup Successful at ' + datetime.datetime.now().strftime("%m-%d-%Y-%H:%M:%S")
            database_entry(args.maindb, args.dbuser, args.dbpassword, args.dbname, res.get('filename'), args.processid, backup_dir+'/', backup_file_path, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), status="Success", message=msg)
            return {
                'success': True,
                'msg': msg
            }
        except Exception as e:
            msg = 'Failed at ' + datetime.datetime.now().strftime("%m-%d-%Y-%H:%M:%S") + ' ' + str(e)
            database_entry(args.maindb, args.dbuser, args.dbpassword, args.dbname, res.get('filename') if res else '', args.processid, backup_dir+'/', backup_file_path if backup_file_path else '', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), status="Failure", message=msg)
            return {
                'success': False,
                'msg': msg
            }

if __name__ == '__main__':
    args = init_parser()
    print(backup_db())
    # database_entry("postgres", "postgres", "postgres", 'test_db', os.getcwd(), os.getpid(), os.getcwd(), '', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


