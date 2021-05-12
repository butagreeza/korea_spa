# -*- coding: utf-8 -*-
from _thread import _local
from odoo import http
import logging
from odoo.exceptions import except_orm
import odoo.addons.web.controllers.main as base_main
_logger = logging.getLogger(__name__)


class DataSet(base_main.DataSet):
    """
        Các model không phân quyền được bằng record rule thì phân quyền ở đây.
    """
    def do_search_read(self, model, fields=False, offset=0, limit=False, domain=None, sort=None, context=None):
        def _get_izi_service_card_using_line_via_doctor(doctor):
            query = ''' SELECT a.id FROM izi_service_card_using_line a LEFT JOIN hr_employee_tour_izi_service_card_using_line_rels b ON a.id = b.izi_service_card_using_line_id LEFT JOIN izi_service_card_using c ON c.id = a.using_id WHERE b.hr_employee_id = %s AND c.state in ('wait_material','working','rate') '''
            cr.execute(query, (doctor.id, ))
            res = cr.dictfetchall()
            if not res:
                return False
            else:
                izi_service_card_using_line_ids = []
                for r in res:
                    izi_service_card_using_line_ids.append(r['id'])
                return izi_service_card_using_line_ids

        def _get_izi_service_card_using_line_via_employee(employee):
            query = ''' SELECT a.id FROM izi_service_card_using_line a LEFT JOIN hr_employee_izi_service_card_using_line_rel b ON a.id = b.izi_service_card_using_line_id LEFT JOIN izi_service_card_using c ON c.id = a.using_id WHERE b.hr_employee_id = %s AND c.state in ('wait_material','working','rate') '''
            cr.execute(query, (employee.id, ))
            res = cr.dictfetchall()
            if not res:
                return False
            else:
                izi_service_card_using_line_ids = []
                for r in res:
                    izi_service_card_using_line_ids.append(r['id'])
                return izi_service_card_using_line_ids

        def _get_pos_work_service_allocation_via_employee(employee):
            query = ''' SELECT a.id FROM pos_work_service_allocation a LEFT JOIN pos_work_service_allocation_line b ON a.id = b.pos_work_service_id WHERE b.employee_id = %s '''
            cr.execute(query, (employee.id, ))
            res = cr.dictfetchall()
            if not res:
                return False
            else:
                pos_work_service_allocation_ids = []
                for r in res:
                    pos_work_service_allocation_ids.append(r['id'])
                return pos_work_service_allocation_ids

        uid = http.request.env.uid
        cr = http.request.cr
        UserObj = http.request.env['res.users']
        TeamObj = http.request.env['crm.team']
        EmployeeObj = http.request.env['hr.employee']
        user = UserObj.sudo().search([('id', '=', uid)], limit=1)
        group_erp_manager = UserObj.has_group('base.group_erp_manager')
        if uid != 1:
            if not user.branch_ids: raise except_orm('Thông báo', 'Người dùng %s chưa chọn chi nhánh cho phép. Vui lòng liên hệ quản trị để được giải quyết' % (
                                                                   str(user.name)))
            for branch in user.branch_ids:
                if not branch: raise except_orm('Thông báo', 'Chi nhánh %s chưa chọn thương hiệu. Vui lòng liên hệ quản trị để được giải quyết' % (
                                                                        str(branch.name)))
            branch_ids = [user.branch_id and user.branch_id.id or 0]
            for branch in user.branch_ids:
                branch_ids.append(branch.id)
            if domain == None:
                domain = []
            if model == 'izi.service.card.using.line':
                if not group_erp_manager:
                    group_receptionist = UserObj.has_group('izi_res_permissions.group_receptionist')
                    group_therapist = UserObj.has_group('izi_res_permissions.group_therapist')

                    group_business_manager = UserObj.has_group('izi_res_permissions.group_business_manager')
                    group_revenue_accountant = UserObj.has_group('izi_res_permissions.group_revenue_accountant')
                    group_cost_accountant = UserObj.has_group('izi_res_permissions.group_cost_accountant')
                    group_revenue_control = UserObj.has_group('izi_res_permissions.group_revenue_control')
                    if group_revenue_control or group_business_manager or group_revenue_accountant or group_cost_accountant:
                        domain += [('using_id.pos_session_id.branch_id', 'in', branch_ids), ('using_id.state', 'in', ('wait_material','working','rate'))]
                    elif group_receptionist:
                        if not user.x_pos_config_id: raise except_orm('Thông báo', 'Tài khoản của bạn chưa gắn điểm bán hàng. Vui lòng liên hệ quản trị viên để được hướng dẫn.')
                        if not user.x_pos_config_id.crm_team_id: raise except_orm('Thông báo', 'Điểm bán hàng %s chưa chọn nhóm bán hàng. Vui lòng liên hệ quản trị viên để được hướng dẫn.' % (str(user.x_pos_config_id.name)))
                        if not user.x_pos_config_id.crm_team_id.x_member_ids: raise except_orm('Thông báo', 'Nhóm bán hàng %s chưa có thành viên nào. Vui lòng liên hệ quản trị viên để được hướng dẫn' % (str(user.x_pos_config_id.crm_team_id.name), ))
                        izi_service_card_using_line_ids = []
                        for member in user.x_pos_config_id.crm_team_id.x_member_ids:
                            employee = EmployeeObj.search([('user_id', '=', member.id)])
                            if not employee: raise except_orm('Thông báo', 'Tài khoản của nhân viên trong cơ sở bạn (%s) chưa được gắn vào nhân viên nào. Vui lòng liên hệ quản trị viên để được hướng dẫn.' % (str(member.name)))
                            if len(employee) > 1: raise except_orm('Thông báo', 'Đang tồn tại %s nhân viên cùng được cấu hình người dùng %s. Vui lòng cấu hình lại trước khi thực hiện thao tác.' % (str(len(employee)), str(member.name)))

                            list_using_line_employee = _get_izi_service_card_using_line_via_employee(employee) and _get_izi_service_card_using_line_via_employee(employee) or []
                            list_using_line_doctor = _get_izi_service_card_using_line_via_doctor(employee) and _get_izi_service_card_using_line_via_doctor(employee) or []
                            izi_service_card_using_lines = list_using_line_employee + list_using_line_doctor
                            if izi_service_card_using_lines:
                                izi_service_card_using_line_ids += izi_service_card_using_lines
                        if izi_service_card_using_line_ids:
                            domain = [['id', 'in', izi_service_card_using_line_ids]]
                        else:
                            domain+=[['id', '=', 0]]

                    elif group_therapist:
                        employee = EmployeeObj.search([('user_id', '=', user.id)])
                        if not employee: raise except_orm('Thông báo', 'Tài khoản của bạn chưa được gắn vào nhân viên nào. Vui lòng liên hệ quản trị viên để được hướng dẫn.')
                        izi_service_card_using_line_ids = _get_izi_service_card_using_line_via_employee(employee)
                        if izi_service_card_using_line_ids:
                            domain = [['id', 'in', izi_service_card_using_line_ids]]
                        else:
                            domain+=[['id', '=', 0]]
                    else:
                        domain+=[['id', '=', 0]]
            elif model == 'crm.lead':
                if not group_erp_manager:
                    group_receptionist = UserObj.has_group('izi_res_permissions.group_receptionist')
                    group_consultant = UserObj.has_group('izi_res_permissions.group_consultant')
                    group_leader_uid_telesales = UserObj.has_group('izi_res_permissions.group_leader_telesales')
                    group_member_uid_telesales = UserObj.has_group('izi_res_permissions.group_telesales')
                    group_social_network_administrator = UserObj.has_group('izi_res_permissions.group_social_network_administrator')
                    group_leader_social_network_administrator = UserObj.has_group('izi_res_permissions.group_leader_social_network_administrator')
                    group_leader_customer_care = UserObj.has_group('izi_res_permissions.group_leader_customer_care')
                    group_customer_care = UserObj.has_group('izi_res_permissions.group_customer_care')

                    if group_receptionist:
                        teams = TeamObj.search([('x_member_ids', 'in', (uid,))])
                        member_ids = []
                        for team in teams:
                            for member in team.x_member_ids:
                                member_ids.append(member.id)
                        domain += [('x_state', 'in', ['meeting', 'to_shop', 'confirm', 'won']), ('team_id.x_member_ids', 'in', (uid,))]
                    elif group_consultant:
                        domain += ['|', ('user_id', '=', uid), ('create_uid', '=', uid)]
                    elif group_leader_uid_telesales:
                        domain += [('telesale_id', '!=', False)]
                    elif group_member_uid_telesales:
                        domain += [('telesale_id', '=', uid)]
                    elif group_leader_social_network_administrator:
                        domain += []
                    elif group_social_network_administrator:
                        domain += [('create_uid', '=', uid)]
                    elif group_leader_customer_care or group_customer_care:
                        teams = TeamObj.search([('x_member_ids', 'in', (uid,))])
                        domain += [('team_id', 'in', teams.ids), ('x_state', 'in', ['meeting', 'to_shop', 'confirm', 'won'])]
                    else:
                        domain+=[['id', '=', 0]]
            elif model == 'pos.service.room':
                if not group_erp_manager:
                    domain += [('branch_id', 'in', branch_ids)]
            elif model == 'pos.work.service.allocation':
                if not group_erp_manager:
                    group_receptionist = UserObj.has_group('izi_res_permissions.group_receptionist')
                    group_therapist = UserObj.has_group('izi_res_permissions.group_therapist')

                    group_business_manager = UserObj.has_group('izi_res_permissions.group_business_manager')
                    group_revenue_accountant = UserObj.has_group('izi_res_permissions.group_revenue_accountant')
                    group_cost_accountant = UserObj.has_group('izi_res_permissions.group_cost_accountant')
                    group_revenue_control = UserObj.has_group('izi_res_permissions.group_revenue_control')
                    if group_revenue_control or group_business_manager or group_revenue_accountant or group_cost_accountant:
                        domain+=[('pos_session_id.branch_id', 'in', branch_ids)]
                    elif group_receptionist:
                        if not user.x_pos_config_id: raise except_orm('Thông báo', 'Tài khoản của bạn chưa gắn điểm bán hàng. Vui lòng liên hệ quản trị viên để được hướng dẫn.')
                        if not user.x_pos_config_id.crm_team_id: raise except_orm('Thông báo', 'Điểm bán hàng %s chưa chọn nhóm bán hàng. Vui lòng liên hệ quản trị viên để được hướng dẫn.' % (str(user.x_pos_config_id.name)))
                        if not user.x_pos_config_id.crm_team_id.x_member_ids: raise except_orm('Thông báo', 'Nhóm bán hàng %s chưa có thành viên nào. Vui lòng liên hệ quản trị viên để được hướng dẫn' % (str(user.x_pos_config_id.crm_team_id.name), ))
                        pos_work_service_allocation_ids = []
                        for member in user.x_pos_config_id.crm_team_id.x_member_ids:
                            employee = EmployeeObj.search([('user_id', '=', member.id)])
                            if not employee: raise except_orm('Thông báo', 'Tài khoản của nhân viên trong cơ sở bạn (%s) chưa được gắn vào nhân viên nào. Vui lòng liên hệ quản trị viên để được hướng dẫn.' % (str(member.name)))
                            if len(employee) > 1: raise except_orm('Thông báo', 'Đang tồn tại %s nhân viên cùng được cấu hình người dùng %s. Vui lòng cấu hình lại trước khi thực hiện thao tác.' % (str(len(employee)), str(member.name)))
                            pos_work_service_allocations = _get_pos_work_service_allocation_via_employee(employee)
                            if pos_work_service_allocations:
                                pos_work_service_allocation_ids += pos_work_service_allocations
                        if pos_work_service_allocation_ids:
                            domain = [['id', 'in', pos_work_service_allocation_ids]]
                        else:
                            domain+=[['id', '=', 0]]
                    elif group_therapist:
                        employee = EmployeeObj.search([('user_id', '=', user.id)])
                        if not employee: raise except_orm('Thông báo', 'Tài khoản của nhân viên trong cơ sở bạn (%s) chưa được gắn vào nhân viên nào. Vui lòng liên hệ quản trị viên để được hướng dẫn.' % (str(user.name)))
                        if len(employee) > 1: raise except_orm('Thông báo', 'Đang tồn tại %s nhân viên cùng được cấu hình người dùng %s. Vui lòng cấu hình lại trước khi thực hiện thao tác.' % (str(len(employee)), str(user.name)))
                        pos_work_service_allocation_ids = _get_pos_work_service_allocation_via_employee(employee)
                        domain += [('id', 'in', pos_work_service_allocation_ids)]
                    else:
                        domain+=[['id', '=', 0]]
            elif model == 'pos.customer.deposit':
                if not group_erp_manager:
                    group_receptionist = UserObj.has_group('izi_res_permissions.group_receptionist')
                    group_cashier = UserObj.has_group('izi_res_permissions.group_cashier')
                    group_consultant = UserObj.has_group('izi_res_permissions.group_consultant')

                    group_business_manager = UserObj.has_group('izi_res_permissions.group_business_manager')
                    group_revenue_accountant = UserObj.has_group('izi_res_permissions.group_revenue_accountant')
                    group_cost_accountant = UserObj.has_group('izi_res_permissions.group_cost_accountant')
                    group_revenue_control = UserObj.has_group('izi_res_permissions.group_revenue_control')

                    branch_ids = []

                    if group_receptionist or not group_cashier or group_revenue_control or group_business_manager or group_revenue_accountant or group_cost_accountant:
                        branch_ids = [user.branch_id and user.branch_id.id or 0]
                        for branch in user.branch_ids:
                            branch_ids.append(branch.id)
                    if group_consultant and (not group_receptionist or not group_cashier):
                        domain += [['partner_id.user_id', '=', user.id]]

                    if branch_ids:
                        domain += [['partner_id.x_crm_team_id.x_branch_id', 'in', branch_ids]]
            elif model == 'pos.customer.deposit.line':
                if not group_erp_manager:
                    group_receptionist = UserObj.has_group('izi_res_permissions.group_receptionist')
                    group_cashier = UserObj.has_group('izi_res_permissions.group_cashier')
                    group_consultant = UserObj.has_group('izi_res_permissions.group_consultant')

                    group_business_manager = UserObj.has_group('izi_res_permissions.group_business_manager')
                    group_revenue_accountant = UserObj.has_group('izi_res_permissions.group_revenue_accountant')
                    group_cost_accountant = UserObj.has_group('izi_res_permissions.group_cost_accountant')
                    group_revenue_control = UserObj.has_group('izi_res_permissions.group_revenue_control')

                    branch_ids = []

                    if group_receptionist or not group_cashier or group_revenue_control or group_business_manager or group_revenue_accountant or group_cost_accountant:
                        branch_ids = [user.branch_id and user.branch_id.id or 0]
                        for branch in user.branch_ids:
                            branch_ids.append(branch.id)
                    if group_consultant and (not group_receptionist or not group_cashier):
                        domain += [['user_id', '=', user.id]]
                    if branch_ids:
                        domain += [['session_id.branch_id', 'in', branch_ids]]
            elif model == 'therapy.record':
                if not group_erp_manager:
                    group_doctor = UserObj.has_group('izi_res_permissions.group_doctor')
                    group_consultant = UserObj.has_group('izi_res_permissions.group_consultant')
                    group_leader_consultant = UserObj.has_group('izi_res_permissions.group_leader_consultant')
                    group_cashier = UserObj.has_group('izi_res_permissions.group_cashier')
                    group_receptionist = UserObj.has_group('izi_res_permissions.group_receptionist')

                    if group_cashier or group_doctor or group_receptionist:
                        domain += [['partner_id.x_crm_team_id.x_branch_id', '=', user.branch_id.id]]
                    elif group_consultant:
                        domain += [['partner_id.user_id', '=', uid]]
            elif model == 'therapy.prescription':
                if not group_erp_manager:
                    group_doctor = UserObj.has_group('izi_res_permissions.group_doctor')
                    group_consultant = UserObj.has_group('izi_res_permissions.group_consultant')
                    group_cashier = UserObj.has_group('izi_res_permissions.group_cashier')
                    group_leader_consultant = UserObj.has_group('izi_res_permissions.group_leader_consultant')
                    group_receptionist = UserObj.has_group('izi_res_permissions.group_receptionist')
                    group_customer_care = UserObj.has_group('izi_res_permissions.group_customer_care')
                    if group_doctor or group_cashier or group_leader_consultant or group_receptionist or group_customer_care:
                        domain += [['partner_id.x_crm_team_id.x_branch_id', '=', user.branch_id.id]]
                    elif group_consultant:
                        domain += [['partner_id.user_id', '=', uid]]
                    else:
                        domain += [['id', '=', 0]]
            elif model == 'therapy.bundle':
                if not group_erp_manager:
                    group_consultant = UserObj.has_group('izi_res_permissions.group_consultant')
                    if group_consultant:
                        domain += [['partner_id.user_id', '=', uid]]
                    else:
                        domain += [['id', '=', 0]]
            elif model == 'activity.history':
                if not group_erp_manager:
                    group_consultant = UserObj.has_group('izi_res_permissions.group_consultant')
                    group_telesales = UserObj.has_group('izi_res_permissions.group_telesales')
                    group_customer_care = UserObj.has_group('izi_res_permissions.group_customer_care')
                    group_leader_customer_care = UserObj.has_group('izi_res_permissions.group_leader_customer_care')
                    group_leader_telesales = UserObj.has_group('izi_res_permissions.group_leader_telesales')
                    if group_leader_customer_care or group_customer_care:
                        domain += [['partner_id.x_crm_team_id.x_branch_id', '=', user.branch_id.id]]
                    elif group_leader_telesales:
                        domain += [['partner_id.x_crm_team_id.x_branch_id', '=', user.branch_id.id], ['object', '=', 'telesale']]
                    elif group_consultant or group_telesales:
                        domain += [['user_id', '=', uid]]
                    else:
                        domain += [['id', '=', 0]]
            elif model == 'service.booking':
                if not group_erp_manager:
                    #Lễ tân
                    group_receptionist = UserObj.has_group('izi_res_permissions.group_receptionist')
                    if not group_receptionist:
                        domain += ['|', ('create_uid', '=', uid), ('type', '=', 'service')]
            else:
                pass

        return super(DataSet, self).do_search_read(model, fields, offset, limit, domain, sort)

