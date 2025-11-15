/** @odoo-module **/

import { Component, useState, onMounted, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";

class SmartImportMapping extends Component {
    setup() {
        this.mappingContainer = useRef("mappingContainer");
        this.state = useState({
            csvHeaders: [],
            availableFields: [],
            mappings: {}
        });

        onMounted(() => {
            this.loadMappingData();
            this.renderMappingInterface();
        });
    }

    loadMappingData() {
        // Get headers from form
        const headersElement = document.querySelector('[name="headers"]');
        const fieldsElement = document.querySelector('[name="available_fields"]');
        
        if (headersElement && headersElement.value) {
            try {
                this.state.csvHeaders = JSON.parse(headersElement.value);
            } catch (e) {
                console.error("Error parsing headers:", e);
            }
        }

        if (fieldsElement && fieldsElement.value) {
            try {
                this.state.availableFields = JSON.parse(fieldsElement.value);
            } catch (e) {
                console.error("Error parsing available fields:", e);
            }
        }
    }

    renderMappingInterface() {
        const container = document.getElementById('csv_column_mapping');
        if (!container || !this.state.csvHeaders.length) {
            return;
        }

        let html = '<div class="row"><div class="col-12">';
        html += '<table class="table table-sm table-bordered">';
        html += '<thead class="table-light">';
        html += '<tr><th>CSV Column</th><th>Odoo Field</th><th>Sample Data</th></tr>';
        html += '</thead><tbody>';

        this.state.csvHeaders.forEach((header, index) => {
            html += '<tr>';
            html += `<td><strong>${header}</strong></td>`;
            html += '<td>';
            html += `<select class="form-select form-select-sm" data-column-index="${index}" onchange="updateMapping(${index}, this.value)">`;
            html += '<option value="">-- Select Odoo Field --</option>';
            
            // Group fields by type
            const fieldGroups = {
                'Basic Fields': [],
                'Relational Fields': [],
                'Other Fields': []
            };

            this.state.availableFields.forEach(field => {
                if (field.name.includes('/')) {
                    fieldGroups['Relational Fields'].push(field);
                } else if (['char', 'text', 'float', 'integer', 'boolean', 'date', 'datetime'].includes(field.type)) {
                    fieldGroups['Basic Fields'].push(field);
                } else {
                    fieldGroups['Other Fields'].push(field);
                }
            });

            // Add optgroups
            Object.entries(fieldGroups).forEach(([groupName, fields]) => {
                if (fields.length > 0) {
                    html += `<optgroup label="${groupName}">`;
                    fields.forEach(field => {
                        const selected = this.state.mappings[index] === field.name ? 'selected' : '';
                        html += `<option value="${field.name}" ${selected}>${field.string} (${field.name})</option>`;
                    });
                    html += '</optgroup>';
                }
            });

            html += '</select>';
            html += '</td>';
            html += '<td class="text-muted"><small>Sample data will appear here</small></td>';
            html += '</tr>';
        });

        html += '</tbody></table>';
        html += '</div></div>';

        container.innerHTML = html;

        // Add global function for mapping updates
        window.updateMapping = (columnIndex, fieldName) => {
            this.state.mappings[columnIndex] = fieldName;
            this.updateMappingData();
        };
    }

    updateMappingData() {
        // Update the hidden mapping_data field
        const mappingElement = document.querySelector('[name="mapping_data"]');
        if (mappingElement) {
            mappingElement.value = JSON.stringify(this.state.mappings);
        }
    }
}

SmartImportMapping.template = "supplier_pricelist_sync.SmartImportMapping";

// Register as a widget
registry.category("fields").add("smart_import_mapping", SmartImportMapping);