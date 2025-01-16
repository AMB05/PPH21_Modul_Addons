# -*- coding: utf-8 -*-
# from odoo import http


# class Pph21Module(http.Controller):
#     @http.route('/pph21_module/pph21_module', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pph21_module/pph21_module/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('pph21_module.listing', {
#             'root': '/pph21_module/pph21_module',
#             'objects': http.request.env['pph21_module.pph21_module'].search([]),
#         })

#     @http.route('/pph21_module/pph21_module/objects/<model("pph21_module.pph21_module"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pph21_module.object', {
#             'object': obj
#         })
