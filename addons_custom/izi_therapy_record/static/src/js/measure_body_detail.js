odoo.define('izi_therapy_record.widget', function(require) {
"use strict";


var AbstractField = require('web.AbstractField');
var core = require('web.core');
var registry = require('web.field_registry');
var _t = core._t;
var qweb = core.qweb;
var rpc = require('web.rpc');

var TherapyBundleBodyMeasure = AbstractField.extend({
    custom_events: _.extend({}, AbstractField.prototype.custom_events, {
        'field_changed': '_onFieldChanged',
    }),

    init: function () {
        this._super.apply(this, arguments);
    },

    _render: function () {
        this._super.apply(this, arguments);
        this._rednder_element();
    },

    _rednder_element: function () {
        // var obj = this.getMainObject();
        var self = this;
        var therapy_id = this.res_id;
        return rpc.query({
                model: this.model,
                method: 'get_measure_body_detail_therapy_record',
                args: [therapy_id],
            }).then(function (res) {
            self.$el.append($(qweb.render("izi_therapy_record.BodyMeasureDetail", {widget: this, items: res[0], arr_body: res[1]})));
        })

    },
    });
registry.add('measure_body_detail', TherapyBundleBodyMeasure);
});

