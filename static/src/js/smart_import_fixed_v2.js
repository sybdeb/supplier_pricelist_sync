/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

/**
 * Smart Import - Fixed Version 2 
 * Pure JavaScript state, minimal server interaction
 */
export class SmartImportFixedV2 extends Component {
    static template = "supplier_pricelist_sync.SmartImportFixedV2";

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        // PURE JAVASCRIPT STATE (zero server state dependency)
        this.state = useState({
            // Step management
            currentStep: 'select_supplier', // select_supplier -> upload_file -> map_columns -> ready
            
            // Data
            supplier_id: null,
            availableSuppliers: [],
            csvFile: null,
            csvHeaders: [],
            csvRows: [],
            mappings: {},
            
            // UI
            isProcessing: false
        });

        // Load suppliers immediately  
        this.loadSuppliers();
    }

    async loadSuppliers() {
        try {
            this.state.availableSuppliers = await this.orm.searchRead(
                'res.partner', 
                [['supplier_rank', '>', 0]], 
                ['id', 'name']
            );
        } catch (error) {
            this.notification.add(_t("Failed to load suppliers"), { type: "danger" });
        }
    }

    onSupplierSelect(ev) {
        this.state.supplier_id = parseInt(ev.target.value);
        if (this.state.supplier_id) {
            this.state.currentStep = 'upload_file';
        }
    }

    async onFileUpload(ev) {
        const file = ev.target.files[0];
        if (!file || !file.name.endsWith('.csv')) {
            this.notification.add(_t("Please select a CSV file"), { type: "danger" });
            return;
        }

        this.state.isProcessing = true;

        try {
            // Parse CSV in JavaScript (no server call)
            const text = await file.text();
            const rows = text.split('\n').map(row => row.split(','));
            
            if (rows.length < 2) {
                throw new Error("CSV must have at least 2 rows (header + data)");
            }

            // Update JavaScript state directly
            this.state.csvFile = file;
            this.state.csvHeaders = rows[0];
            this.state.csvRows = rows.slice(1, 6); // First 5 data rows for preview
            this.state.currentStep = 'map_columns';
            
            // Auto-generate mappings
            this.autoGenerateMappings();

            this.notification.add(_t("CSV parsed successfully!"), { type: "success" });

        } catch (error) {
            this.notification.add(_t("CSV parsing failed: ") + error.message, { type: "danger" });
        } finally {
            this.state.isProcessing = false;
        }
    }

    autoGenerateMappings() {
        const mappings = {};
        
        this.state.csvHeaders.forEach((header, index) => {
            const lower = header.toLowerCase();
            let odooField = '';

            if (lower.includes('ean') || lower.includes('barcode')) {
                odooField = 'import_barcode';
            } else if (lower.includes('sku') || lower.includes('fabrikantscode')) {
                odooField = 'import_sku';
            } else if (lower.includes('prijs') || lower.includes('price')) {
                odooField = 'price';
            } else if (lower.includes('voorraad') || lower.includes('qty')) {
                odooField = 'import_qty_available';
            }

            mappings[index] = odooField;
        });

        this.state.mappings = mappings;
        
        if (Object.values(mappings).some(v => v)) {
            this.state.currentStep = 'ready';
        }
    }

    onMappingChange(columnIndex, newField) {
        // Instant JavaScript state update
        this.state.mappings[columnIndex] = newField;
        
        // Check if ready for import
        const hasMappings = Object.values(this.state.mappings).some(v => v);
        this.state.currentStep = hasMappings ? 'ready' : 'map_columns';
    }

    async saveTemplate() {
        this.state.isProcessing = true;

        try {
            // Single server call to save template
            await this.orm.call('supplier.smart.import.stateless', 'save_template', [{
                supplier_id: this.state.supplier_id,
                mappings: this.state.mappings,
                headers: this.state.csvHeaders
            }]);

            // JavaScript state remains unchanged
            this.notification.add(_t("Template saved!"), { type: "success" });

        } catch (error) {
            this.notification.add(_t("Save failed: ") + error.message, { type: "danger" });
        } finally {
            this.state.isProcessing = false;
        }
    }

    async executeImport() {
        this.state.isProcessing = true;

        try {
            // Parse full CSV for import
            const fullText = await this.state.csvFile.text();
            
            // Single server call for import
            const result = await this.orm.call('supplier.smart.import.stateless', 'execute_full_import', [{
                supplier_id: this.state.supplier_id,
                mappings: this.state.mappings,
                csv_content: fullText
            }]);

            // JavaScript state remains unchanged
            this.notification.add(_t(`Import completed: ${result.created} created, ${result.updated} updated`), {
                type: "success"
            });

        } catch (error) {
            this.notification.add(_t("Import failed: ") + error.message, { type: "danger" });
        } finally {
            this.state.isProcessing = false;
        }
    }

    resetWizard() {
        // Reset to initial state (pure JavaScript)
        this.state.currentStep = 'select_supplier';
        this.state.supplier_id = null;
        this.state.csvFile = null;
        this.state.csvHeaders = [];
        this.state.csvRows = [];
        this.state.mappings = {};
    }
}

registry.category("actions").add("smart_import_fixed_v2", SmartImportFixedV2);