# -*- coding: utf-8 -*-

# Created on 2017-11-05
# author: 广州尚鹏，http://www.sunpop.cn
# email: 300883@qq.com
# resource of Sunpop
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# Odoo在线中文用户手册（长期更新）
# http://www.sunpop.cn/documentation/user/10.0/zh_CN/index.html

# Odoo10离线中文用户手册下载
# http://www.sunpop.cn/odoo10_user_manual_document_offline/
# Odoo10离线开发手册下载-含python教程，jquery参考，Jinja2模板，PostgresSQL参考（odoo开发必备）
# http://www.sunpop.cn/odoo10_developer_document_offline/
# description:
from openerp import models, fields, api, exceptions,  _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    default_code = fields.Char('Internal Reference', index=True, default='New', copy=False)
    default_code_index = fields.Integer('Internal Reference Index',  readonly=True)

    # todo: 检查数据，要保证数据唯一性
    # 为免报错，不限制唯一性
    # _sql_constraints = [
    #     ('uniq_default_code',
    #      'unique(default_code)',
    #      'The reference must be unique'),
    # ]

    @api.model
    def create(self, vals):
        # todo: but 先建空白产品后，编辑2个以上变体，序号会少个 -1
        # code_index: 当没有变体现时，值为0，有变体时，为该变体序号
        if 'default_code' not in vals or vals['default_code'] == 'New':
            code_index = 0
            if 'product_tmpl_id' in vals:
                template = self.env['product.template'].search([('id', '=', vals['product_tmpl_id'])], limit=1)
                mylen = len(template.product_variant_ids)
            if 'product_tmpl_id' in vals:
            # created from product_template
                template = self.env['product.template'].search([('id', '=', vals['product_tmpl_id'])], limit=1)
                attr = vals['attribute_value_ids'][0][2]
                if not(attr):
                    # 没有属性值，则是单规格产品。attribute_value_ids格式为[6,0,[]]。多规格时，attribute_value_ids格式为[6,0,[x]]
                    code_index = 0
                    vals['default_code_index'] = code_index
                    vals['default_code'] = template.default_code_stored
                elif mylen == 0:
                    # 有属性值了，自己是第一个规格
                    code_index = 1
                    vals['default_code_index'] = code_index
                    vals['default_code'] = template.default_code_stored + '-%03d'%(code_index)
                elif mylen == 1:
                    # 已存在1个，当存在的1个有属性时，要改已存在的product值
                    code_index = template.product_variant_ids[:1].default_code_index
                    if template.product_variant_ids[:1].attribute_value_ids:
                        if code_index == 0:
                            code_index = 1
                        template.product_variant_ids[:1].default_code_index = code_index
                        template.product_variant_ids[:1].default_code = template.default_code_stored + '-%03d'%(code_index)
                    # 接着改当前操作的product值
                    code_index = code_index + 1
                    vals['default_code_index'] = code_index
                    vals['default_code'] = template.default_code_stored + '-%03d'%(code_index)
                else:
                    # 找到最大的序号
                    variant_max = max(template.product_variant_ids,key=lambda x: x['default_code_index'])
                    code_index = variant_max['default_code_index'] + 1
                    vals['default_code_index'] = code_index
                    vals['default_code'] = template.default_code_stored + '-%03d'%(code_index)
            else:
                # create from product_product
                sequence = self.env['product.internal.type'].search([('id', '=', vals['internal_type'])], limit=1)
                if not sequence:
                    sequence = self.env.ref('app_product_type_sequence.internal_type_mrp_product', raise_if_not_found=False)
                if sequence:
                    vals['default_code'] = sequence.link_sequence.next_by_id()
        else:
            # 如果有自己输入 ref，则不需要自运输生成
            # sequence = self.env['product.internal.type'].search([('id', '=', vals['internal_type'])], limit=1)
            # if sequence:
            #     vals['default_code'] = sequence.link_sequence.next_by_id()
            pass
        return super(ProductProduct, self).create(vals)

    @api.multi
    def copy(self, default=None):
        if len(self.product_tmpl_id.product_variant_ids)>1 :
            raise exceptions.ValidationError(_('Product varient can only create in Product view!'))
        return super(ProductProduct, self).copy(default=None)

    # 当内部类型变化时，改变产品模板的各默认值
    @api.onchange('internal_type')
    def _onchange_internal_type(self):
        if self.internal_type:
            self.type = self.internal_type.type
            self.rental = self.internal_type.rental
            self.sale_ok = self.internal_type.sale_ok
            self.purchase_ok = self.internal_type.purchase_ok
            self.route_ids = self.internal_type.route_ids

    # 分类变动时，如果分类绑定了内部类型则联动
    @api.onchange('categ_id')
    def _onchange_cate_id(self):
        if self.categ_id and self.categ_id.internal_type:
            self.internal_type = self.categ_id.internal_type