/** @odoo-module **/

import { Component, onWillStart, useRef, useState } from "@odoo/owl";
import { useDropzone } from "@web/core/dropzone/dropzone_hook";
import { FileInput } from "@web/core/file_input/file_input";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useFileUploader } from "@web/core/utils/files";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

/**
 * Smart Import - Fixed Version 1
 * Based on Odoo's native ImportAction architecture
 */
export class SmartImportFixedV1 extends Component {
    static template = "supplier_pricelist_sync.SmartImportFixedV1";
    static components = {
        FileInput,
    };
    static props = { ...standardActionServiceProps };

    setup() {
        this.actionService = useService("action");
        this.notification = useService("notification");
        this.orm = useService("orm");

        // PERSISTENT CLIENT STATE (like Odoo's native import)
        this.state = useState({
            // File state
            filename: undefined,
            
            // CSV data
            csvHeaders: [],
            csvPreview: [],
            
            // Supplier & mapping
            supplier_id: null,
            availableSuppliers: [],
            mappingLines: [],
            
            // UI state
            showPreview: false,
            isProcessing: false
        });

        // File upload handler (like native import)
        this.uploadFiles = useFileUploader();
        
        // Drag & drop (like native import)
        useDropzone(useRef("root"), async (event) => {
            const { files } = event.dataTransfer;
            if (files.length === 0) {
                this.notification.add(_t("Please upload a CSV file."), { type: "danger" });
            } else if (files.length > 1) {
                this.notification.add(_t("Please upload a single file."), { type: "danger" });
            } else {
                await this.handleFileUpload(files[0]);
            }
        });

        onWillStart(async () => {
            // Load suppliers
            this.state.availableSuppliers = await this.orm.searchRead(
                'res.partner', 
                [['supplier_rank', '>', 0]], 
                ['id', 'name']
            );
        });
    }

    async handleFileUpload(file) {
        if (!file.name.endsWith('.csv')) {
            this.notification.add(_t("Please upload a CSV file."), { type: "danger" });
            return;
        }

        if (!this.state.supplier_id) {
            this.notification.add(_t("Please select a supplier first."), { type: "danger" });
            return;
        }

        this.state.isProcessing = true;

        try {
            // Create base_import.import record (like native)
            const importRecord = await this.orm.create('base_import.import', [{
                'res_model': 'product.supplierinfo',
                'file_name': file.name,
                'file_type': 'text/csv'
            }]);

            // Upload file via native route (like native import)
            await this.uploadFiles('/base_import/set_file', {
                csrf_token: odoo.csrf_token,
                ufile: [file],
                id: importRecord
            });

            // Parse preview (like native)
            const preview = await this.orm.call('base_import.import', 'parse_preview', [
                importRecord,
                { 'separator': ',', 'quoting': '"', 'encoding': 'utf-8' }
            ]);

            // Update CLIENT STATE (no server state!)
            this.state.filename = file.name;
            this.state.csvHeaders = preview.headers;
            this.state.csvPreview = preview.preview;
            this.state.showPreview = true;
            this.state.mappingLines = this.autoMapColumns(preview.headers);

            this.notification.add(_t("File uploaded successfully!"), { type: "success" });

        } catch (error) {
            this.notification.add(_t("Upload failed: ") + error.message, { type: "danger" });
        } finally {
            this.state.isProcessing = false;
        }
    }

    autoMapColumns(headers) {
        const mappings = [];
        const lowerHeaders = headers.map(h => h.toLowerCase());

        headers.forEach((header, index) => {
            const lowerHeader = lowerHeaders[index];
            let odooField = '';

            // Auto-mapping logic (same as before)
            if (lowerHeader.includes('ean') || lowerHeader.includes('barcode')) {
                odooField = 'import_barcode';
            } else if (lowerHeader.includes('sku') || lowerHeader.includes('fabrikantscode')) {
                odooField = 'import_sku'; 
            } else if (lowerHeader.includes('prijs') || lowerHeader.includes('price')) {
                odooField = 'price';
            } else if (lowerHeader.includes('voorraad') || lowerHeader.includes('qty')) {
                odooField = 'import_qty_available';
            }

            mappings.push({
                csv_column: header,
                odoo_field: odooField
            });
        });

        return mappings;
    }

    onSupplierChange(ev) {
        const supplierId = parseInt(ev.target.value);
        this.state.supplier_id = supplierId;
    }

    onMappingChange(index, newField) {
        // Update mapping in CLIENT STATE (instant, no server call)
        this.state.mappingLines[index].odoo_field = newField;
    }

    async saveAsTemplate() {
        if (!this.state.supplier_id || !this.state.mappingLines.length) {
            this.notification.add(_t("Complete mapping first."), { type: "danger" });
            return;
        }

        this.state.isProcessing = true;

        try {
            // Save template (server call but state stays intact)
            await this.orm.call('supplier.smart.import.stateless', 'save_mapping_template', [{
                supplier_id: this.state.supplier_id,
                mappings: this.state.mappingLines
            }]);

            // CLIENT STATE BLIJFT INTACT
            this.notification.add(_t("Template saved successfully!"), { type: "success" });

        } catch (error) {
            this.notification.add(_t("Save failed: ") + error.message, { type: "danger" });
        } finally {
            this.state.isProcessing = false;
        }
    }

    async executeImport() {
        if (!this.state.supplier_id || !this.state.mappingLines.length) {
            this.notification.add(_t("Complete mapping first."), { type: "danger" });
            return;
        }

        this.state.isProcessing = true;

        try {
            // Execute import (server call but state stays intact)
            const result = await this.orm.call('supplier.smart.import.stateless', 'execute_import', [{
                supplier_id: this.state.supplier_id,
                mappings: this.state.mappingLines,
                csv_data: this.state.csvPreview
            }]);

            // CLIENT STATE BLIJFT INTACT  
            this.notification.add(_t(`Import completed: ${result.message}`), { 
                type: result.success ? "success" : "warning" 
            });

        } catch (error) {
            this.notification.add(_t("Import failed: ") + error.message, { type: "danger" });
        } finally {
            this.state.isProcessing = false;
        }
    }
}

// Register as client action (not replacing existing)
registry.category("actions").add("smart_import_fixed_v1", SmartImportFixedV1);