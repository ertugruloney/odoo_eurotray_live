# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from . lib import check_connectivity, saas_client_backup


import logging
import base64
import os

_logger = logging.getLogger(__name__)

STATE = [
    ('draft', "Draft"),
    ('validated', 'Validated'),
]

class BackupRemoteServer(models.Model):
    _name = 'backup.remote.server'
    _description="Backup Remote Server"

    name = fields.Char(string="Name", help="Name of the backup remote server")
    sftp_host = fields.Char(string="SFTP Host", help="SFTP host for establishing connection to the backup remote server")
    sftp_port = fields.Char(string="SFTP Port", default="22", help="SFTP port for establishing connection to the backup remote server")
    sftp_user = fields.Char(string="User", help="SFTP user for establishing connection to the backup remote server")
    sftp_password = fields.Char(string="Password", help="SFTP password for establishing connection to the backup remote server")

    state = fields.Selection(selection=STATE, string="State", default="draft", help="State of the backup remote server")
    active = fields.Boolean(string="Active", default=True)
    temp_backup_dir = fields.Char(string="Temporary Backup Directory", help="The temporary backup path where the backups are stored before moving to the remote server. The temporary backup directory must be present on the main server along with the appropriate permissions.")
    def_backup_dir = fields.Char(string="Default Remote Backup Directory", help="The default directory path on the remote server where the backups of the saas client instances will be stored. The directory must have appropriate permissions.")
    
    
    
    
    def test_host_connection(self):
        """ 
        Method to check Host connection: called by the button 'Test Connection'
        """
        
        for obj in self:
            response = obj.check_host_connected_call()
            if response.get('status'):
                message = self.env['backup.custom.message.wizard'].create({'message':"Connection successful!"})
                action = self.env.ref('wk_backup_restore.action_backup_custom_message_wizard').read()[0]
                action['res_id'] = message.id
                return action
            else:
                raise UserError(response.get('message'))
                
    
    def check_host_connected_call(self):
        """
            Method to call the script to check host connectivity, 
            return response dict as per the output.
            Called from 'test_host_connection' and  'set_validated'
        """
        response = dict(
            status=True,
            message='Success'
        )
        host_server = self.get_server_details()
        try:
            response = check_connectivity.ishostaccessible(host_server)
            if response.get('status'):
                _logger.info("======= Remote Server Connection Successful ======")
                ssh_obj = response.get('result')
                backup_dir = self.def_backup_dir
                cmd = "ls %s"%(backup_dir)
                check_path = saas_client_backup.execute_on_remote_shell(ssh_obj,cmd)
                if not check_path.get('status'):
                    raise UserError("Storage path doesn't exist on remote server. Please create the mentioned backup path on the remote server.")
                
                cmd = f"touch {backup_dir}/test.txt"
                create_file = saas_client_backup.execute_on_remote_shell(ssh_obj,cmd)
                if not create_file.get('status'):
                    raise UserError("The mentioned ssh user doesn't have rights to create file. Please provide required permissions on the default backup path.")
                else:
                    cmd = f"rm {backup_dir}/test.txt"
                    delete_file = saas_client_backup.execute_on_remote_shell(ssh_obj,cmd)
                    if delete_file.get('status'):
                        _logger.info("======== Backup Directory Permissions Checked Successfully =========")
        except Exception as e:
            _logger.info(f"------ EXCEPTION WHILE TESTING THE REMOTE SERVER CONNECTION ---- {e} ------")
            response['status'] = False
            response['message'] = e      
        return response
    
    @api.model
    def get_server_details(self):
        """
            Method created to return value of the host server as dict,
            Called from check_host_connected_call method in the complete process
        """
        host_server = dict(
            host=self.sftp_host,
            port=self.sftp_port,
            user=self.sftp_user,
            password=self.sftp_password,
        )
        return host_server

        
    def set_validated(self):
        for obj in self:
            response = obj.check_host_connected_call()
            if response.get('status'):
                obj.state = 'validated'
            else:
                raise UserError(response.get('message'))
    
    def reset_to_draft(self):
        for obj in self:
            bkp_processes = self.env['backup.process'].search([('remote_server_id', '=', obj.id), ('backup_location', '=', 'remote'), ('state', 'in', ['confirm', 'running'])])
            if bkp_processes:
                raise UserError("This Remote Server has some active Backup Process(es)!")
            obj.state = 'draft'
