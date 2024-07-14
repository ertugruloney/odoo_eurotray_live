# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################
import os
import logging
import datetime
import pytz

import odoo
from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError, UserError


_logger = logging.getLogger(__name__) 

class BackupController(http.Controller):


    @http.route('/backupfile/download', type='http', auth='user')
    def file_download(self, **kwargs):
        file_path = request.httprequest.args.get('path')   # The actual file path
        backup_location = request.httprequest.args.get('backup_location') or 'local'
        _logger.info(f"=====backup_location========= {backup_location} ====== file_path ====== {file_path}")
        try:
            # Read the file and return it as a response
            file_data = None
            with open(file_path, 'rb') as file:
                file_data = file.read()

            # Set the response headers for file download
            response = request.make_response(file_data)
            response.headers['Content-Disposition'] = f"attachment; filename={file_path.split('/')[-1]}" 
            response.mimetype = 'application/octet-stream'

            # Delete the remote backup file from Main Server
            if backup_location == 'remote':
                os.remove(file_path)

            return response
        except Exception as e:
            _logger.info(f"======= Backup File Download Error ======= {e} ========")
            raise UserError(e)
 


    @http.route('/saas/database/backup', type='http', auth="none", methods=['POST'], csrf=False)
    def db_backup(self, **kwargs):
        # _logger.info("============ kwargs ======= %r", kwargs)
        master_pwd = kwargs.get('master_pwd')
        dbname = kwargs.get('name')
        backup_format = kwargs.get('backup_format') or 'zip'
        response = None
        data = {"status":True}
        try:
            odoo.service.db.check_super(master_pwd)
            user = request.env['res.users'].sudo().browse([2]) 
            tz = pytz.timezone(user.tz) if user.tz else pytz.utc
            time_now = pytz.utc.localize(datetime.datetime.now()).astimezone(tz)

            ts = time_now.strftime("%m-%d-%Y-%H")
            filename = "%s_%s.%s" % (dbname, ts, backup_format)
            dump_stream = odoo.service.db.dump_db(dbname, None, backup_format)
            backup_dir = kwargs.get('backup_dir')
            backed_up_file_path = os.path.join(backup_dir, filename)
            with open(backed_up_file_path, 'wb') as file:
                file.write(dump_stream.read())
            data['message'] = "Database backup is completed successfully"
            data['filename'] = filename
        except Exception as e:
            error = "Database backup error: %s" % (str(e) or repr(e))
            _logger.exception('Database.backup --- %r', error)
            data = dict(status=False, error_message=error)

        response = request.make_json_response(data)
        return response
