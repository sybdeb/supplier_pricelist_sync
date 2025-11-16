/** @odoo-module **/

import { Component, useState, onMounted, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

/**
 * Smart Import State Manager - Prevents data loss like native base_import
 * 
 * Problem: TransientModel loses data after each action
 * Solution: JavaScript state that persists between server calls
 */
class SmartImportStateManager extends Component {
    static template = "supplier_pricelist_sync.SmartImportStateManager";
    
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        // PERSISTENT STATE - like Odoo's native import
        this.state = useState({
            // CSV Data (persistent)
            csvHeaders: [],
            csvPreview: [],
            csvUploaded: false,
            
            // Mapping Configuration (persistent) 
            mappingLines: [],
            supplier_id: null,
            
            // UI State
            isProcessing: false,
            showPreview: false
        });
        
        onMounted(() => {
            this.initializeFromServer();
        });
    }
    
    async initializeFromServer() {
        // Load any existing wizard data from server
            // No server state needed - pure JavaScript state management
            const wizardData = null;        if (wizardData) {
            this.state.csvHeaders = wizardData.headers || [];
            this.state.csvPreview = wizardData.preview || [];
            this.state.mappingLines = wizardData.mapping_lines || [];
            this.state.supplier_id = wizardData.supplier_id;
            this.state.csvUploaded = wizardData.csv_uploaded || false;
            this.state.showPreview = this.state.csvHeaders.length > 0;
        }
    }
    
    async onFileUpload(ev) {
        const file = ev.target.files[0];
        if (!file) return;
        
        this.state.isProcessing = true;
        
        try {
            // Convert file to base64 (correct format for server)
            const fileData = await new Promise((resolve) => {
                const reader = new FileReader();
                reader.onload = (e) => resolve(e.target.result.split(',')[1]); // Remove data:... prefix
                reader.readAsDataURL(file);
            });
            
            // Call server with correct parameters
            const result = await this.orm.call(
                'supplier.smart.import.stateless',
                'process_csv_upload',
                [fileData, this.state.supplier_id]
            );
            
            // Update JavaScript state (NOT server state) - BLIJFT PERSISTENT
            this.state.csvHeaders = result.headers || [];
            this.state.csvPreview = result.preview || [];  
            this.state.mappingLines = result.mapping_lines || [];
            this.state.csvUploaded = true;
            this.state.showPreview = true;
            
            this.notification.add("CSV uploaded successfully!", { type: "success" });
            
        } catch (error) {
            this.notification.add(`Upload failed: ${error.message}`, { type: "danger" });
        } finally {
            this.state.isProcessing = false;
        }
    }
    
    onMappingChange(lineIndex, newValue) {
        // Update mapping in JavaScript state (instant, no server call)
        this.state.mappingLines[lineIndex].odoo_field = newValue;
    }
    
    async saveAsTemplate() {
        this.state.isProcessing = true;
        
        try {
            await this.orm.call(
                'supplier.smart.import.stateless',
                'save_mapping_template',
                [this.state.supplier_id, this.state.mappingLines]
            );
            
            // State BLIJFT intact - alleen notification
            this.notification.add("Template saved successfully!", { 
                type: "success" 
            });
            
        } catch (error) {
            this.notification.add(`Save failed: ${error.message}`, { type: "danger" });
        } finally {
            this.state.isProcessing = false;
        }
    }
    
    async executeImport() {
        this.state.isProcessing = true;
        
        try {
            const result = await this.orm.call(
                'supplier.smart.import.stateless',
                'execute_import_with_mapping',
                [this.state.supplier_id, this.state.mappingLines]
            );
            
            // State BLIJFT intact - alleen notification
            this.notification.add(`Import completed: ${result.message}`, { 
                type: result.success ? "success" : "warning" 
            });
            
        } catch (error) {
            this.notification.add(`Import failed: ${error.message}`, { type: "danger" });
        } finally {
            this.state.isProcessing = false;
        }
    }
}

// Register the component
registry.category("actions").add("smart_import_js", SmartImportStateManager);