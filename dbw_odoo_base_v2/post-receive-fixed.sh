#!/bin/bash
# Generic Odoo addons deployment hook for DEV environment
# Detects changed modules and triggers upgrade via RPC

# Configuration
DEPLOY_ENV="dev"
ADDONS_BASE="/home/sybren/services/odoo19-${DEPLOY_ENV}/data/addons"
WORK_TREE="/tmp/odoo-deploy-${DEPLOY_ENV}"
LOG_FILE="/var/log/odoo-deployments.log"
RPC_SCRIPT="/home/sybren/scripts/upgrade_module.py"
GIT_DIR="$PWD"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [${DEPLOY_ENV}] $1" | tee -a "$LOG_FILE"
}

log "========== Starting deployment to ${DEPLOY_ENV} =========="

# Read stdin to get branch info
while read oldrev newrev refname; do
    branch=$(git --git-dir="$GIT_DIR" rev-parse --symbolic --abbrev-ref $refname)
    log "Received push to branch: $branch (${oldrev:0:8} -> ${newrev:0:8})"
    
    # Only deploy main/master branch
    if [ "$branch" = "main" ] || [ "$branch" = "master" ]; then
        # Checkout code to temporary directory
        log "Checking out code to ${WORK_TREE}"
        rm -rf "$WORK_TREE"
        mkdir -p "$WORK_TREE"
        git --git-dir="$GIT_DIR" --work-tree="$WORK_TREE" checkout -f "$branch"
        
        # Detect changed modules (top-level directories containing __manifest__.py)
        log "Detecting changed modules..."
        changed_modules=()
        
        # Check if this is a single-module repo (has __manifest__.py in root)
        if [ -f "$WORK_TREE/__manifest__.py" ]; then
            # Single-module repo - derive module name from repo or use git remote name
            log "Single-module repository detected"
            
            # For single module repos, we need to know the target module name
            # Check if there's a .odoo-module file that specifies it
            if [ -f "$WORK_TREE/.odoo-module" ]; then
                module_name=$(cat "$WORK_TREE/.odoo-module" | tr -d '[:space:]')
                log "Module name from .odoo-module: $module_name"
                changed_modules+=("$module_name")
            else
                log "WARNING: Single-module repo without .odoo-module file"
                log "Please create .odoo-module file with target module name"
                log "Example: echo 'dbw_odoo_base_v2' > .odoo-module"
            fi
        else
            # Multi-module repo - original logic
            log "Multi-module repository detected"
            
            if [ "$oldrev" = "0000000000000000000000000000000000000000" ]; then
                # First push - deploy all modules
                log "First push detected - deploying all modules"
                for module_dir in "$WORK_TREE"/*/; do
                    module_name=$(basename "$module_dir")
                    if [ -f "${module_dir}__manifest__.py" ]; then
                        changed_modules+=("$module_name")
                    fi
                done
            else
                # Detect changed files and extract module names
                changed_files=$(git --git-dir="$GIT_DIR" diff --name-only $oldrev $newrev)
                for file in $changed_files; do
                    # Extract module name (first directory in path)
                    module_name=$(echo "$file" | cut -d'/' -f1)
                    # Check if it's a valid module (has __manifest__.py)
                    if [ -f "${WORK_TREE}/${module_name}/__manifest__.py" ]; then
                        # Add to array if not already present
                        if [[ ! " ${changed_modules[@]} " =~ " ${module_name} " ]]; then
                            changed_modules+=("$module_name")
                        fi
                    fi
                done
            fi
        fi
        
        if [ ${#changed_modules[@]} -eq 0 ]; then
            log "No modules changed - nothing to deploy"
        else
            log "Changed modules detected: ${changed_modules[*]}"
            
            # Deploy each changed module
            for module_name in "${changed_modules[@]}"; do
                # Check if single-module repo (source is work tree root)
                if [ -f "$WORK_TREE/__manifest__.py" ]; then
                    source_dir="${WORK_TREE}"
                else
                    source_dir="${WORK_TREE}/${module_name}"
                fi
                
                target_dir="${ADDONS_BASE}/${module_name}"
                
                log "📦 Deploying module: ${module_name}"
                
                # Create target directory if it doesn't exist
                mkdir -p "$target_dir"
                
                # Make target directory writable for current user (temporary)
                sudo chown -R sybren:sybren "$target_dir"
                
                # Sync to target directory (exclude git, tests, cache)
                log "   Syncing ${source_dir} -> ${target_dir}"
                rsync -av --delete \
                    --exclude='.git' \
                    --exclude='.gitignore' \
                    --exclude='tests/' \
                    --exclude='*.pyc' \
                    --exclude='__pycache__/' \
                    --exclude='.pytest_cache/' \
                    --exclude='*.tar.gz' \
                    --exclude='.ruff_cache/' \
                    "${source_dir}/" "${target_dir}/" 2>&1 | grep -v "^sending\|^sent\|^total" | tee -a "$LOG_FILE"
                
                # Fix permissions for Odoo container (after rsync)
                sudo chown -R 101:101 "$target_dir"
                
                # Trigger module upgrade via RPC
                log "   Triggering upgrade via Odoo RPC..."
                if [ -f "$RPC_SCRIPT" ]; then
                    python3 "$RPC_SCRIPT" "$DEPLOY_ENV" "$module_name" 2>&1 | tee -a "$LOG_FILE"
                    if [ $? -eq 0 ]; then
                        log "   ✅ ${module_name} deployed successfully"
                    else
                        log "   ❌ ${module_name} upgrade failed - check logs"
                    fi
                else
                    log "   ⚠️ RPC script not found at $RPC_SCRIPT"
                    log "   Files synced but manual upgrade needed: ${module_name}"
                fi
            done
            
            log "✅ Deployment complete - ${#changed_modules[@]} module(s) processed"
        fi
        
        # Cleanup
        rm -rf "$WORK_TREE"
        log "========== Deployment finished =========="
    else
        log "Ignoring push to branch: $branch (only main/master triggers deployment)"
    fi
done
