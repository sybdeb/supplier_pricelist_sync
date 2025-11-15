#!/usr/bin/env python3
"""
🤖 INTERACTIVE TEST FEEDBACK SYSTEM
Reageert automatisch op test feedback en biedt directe oplossingen
"""

import sys
import json
from datetime import datetime

class TestFeedbackAnalyzer:
    def __init__(self):
        self.issue_patterns = {
            'kolom reset': {
                'solution': 'Mapping preservation system',
                'action': 'Check saved_mapping_state field',
                'status': '✅ FIXED in latest version'
            },
            'unicode error': {
                'solution': 'Arrow character replacement',
                'action': 'Replace → with -> in logs',
                'status': '✅ FIXED - replaced all Unicode arrows'
            },
            'template niet opgeslagen': {
                'solution': 'Database transaction issue',
                'action': 'Check supplier.mapping.template creation',
                'status': '🔍 Check database records'
            },
            'dropdown leeg': {
                'solution': 'Field detection problem',
                'action': 'Check _get_native_odoo_fields method',
                'status': '🔄 Verify hybrid field detection'
            },
            'form reset': {
                'solution': 'TransientModel limitation',
                'action': 'Use wizard reload with preserved state',
                'status': '✅ FIXED - wizard reloads with mappings'
            },
            'csv niet gelezen': {
                'solution': 'Encoding or delimiter issue',
                'action': 'Check CSV parsing in _parse_and_auto_map',
                'status': '🔍 Verify file encoding detection'
            }
        }
    
    def analyze_feedback(self, feedback_text):
        """Analyze user feedback and provide automatic solutions"""
        feedback_lower = feedback_text.lower()
        
        print(f"🤖 ANALYZING FEEDBACK: '{feedback_text}'")
        print("=" * 60)
        
        found_issues = []
        for pattern, details in self.issue_patterns.items():
            if pattern in feedback_lower:
                found_issues.append((pattern, details))
        
        if found_issues:
            print("🎯 IDENTIFIED ISSUES:")
            for pattern, details in found_issues:
                print(f"\n📌 ISSUE: {pattern.upper()}")
                print(f"   💡 SOLUTION: {details['solution']}")
                print(f"   🔧 ACTION: {details['action']}")
                print(f"   📊 STATUS: {details['status']}")
                
                # Automatic fix suggestions
                if pattern == 'kolom reset':
                    self.suggest_mapping_preservation_check()
                elif pattern == 'unicode error':
                    self.suggest_unicode_fix()
                elif pattern == 'dropdown leeg':
                    self.suggest_field_detection_check()
        else:
            print("🔍 No known issues detected. Please describe what specifically is happening:")
            print("   • Are the mappings resetting after save?")
            print("   • Are there error messages in the UI?") 
            print("   • Is the CSV file being parsed correctly?")
            print("   • Are the dropdown fields populated?")
    
    def suggest_mapping_preservation_check(self):
        """Provide specific checks for mapping preservation"""
        print("\n🔧 AUTOMATIC MAPPING PRESERVATION CHECKS:")
        print("   1. Verify saved_mapping_state field exists")
        print("   2. Check _preserve_mapping_state_after_save method")
        print("   3. Confirm wizard reload with preserved context")
        print("   4. Test create() method restoration logic")
    
    def suggest_unicode_fix(self):
        """Provide Unicode error solutions"""
        print("\n🔧 UNICODE ERROR AUTO-FIX:")
        print("   ✅ All → characters replaced with ->")
        print("   ✅ Windows CP1252 encoding compatibility")
        print("   ✅ Log messages sanitized")
    
    def suggest_field_detection_check(self):
        """Provide field detection diagnostics"""
        print("\n🔧 FIELD DETECTION DIAGNOSTICS:")
        print("   1. Check hybrid field detection in smart_import_mapping_line.py")
        print("   2. Verify product.supplierinfo fields are accessible")
        print("   3. Confirm related product fields (barcode, default_code)")
        print("   4. Test _get_native_odoo_fields method")

def main():
    analyzer = TestFeedbackAnalyzer()
    
    print("🤖 INTERACTIVE TEST FEEDBACK SYSTEM")
    print("=" * 50)
    print("Geef feedback over wat je tegenkomt tijdens het testen")
    print("Ik reageer automatisch met oplossingen!")
    print("=" * 50)
    
    print("\n💬 Voorbeelden van feedback:")
    print("   • 'de kolommen resetten na save'")
    print("   • 'unicode error in de logs'") 
    print("   • 'dropdown is leeg'")
    print("   • 'template wordt niet opgeslagen'")
    
    print("\n🎯 Type je feedback (of 'quit' to exit):")
    
    while True:
        try:
            feedback = input("\n👤 FEEDBACK: ").strip()
            if feedback.lower() in ['quit', 'exit', 'q']:
                print("🛑 Test feedback system stopped")
                break
            elif feedback:
                analyzer.analyze_feedback(feedback)
            else:
                print("💡 Geef feedback over wat je tegenkomt tijdens het testen")
                
        except KeyboardInterrupt:
            print("\n🛑 Test feedback system stopped")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()