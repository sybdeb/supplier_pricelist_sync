#!/bin/bash
# Quick Test Commands for Product Supplier Sync PRO
# Run these commands on hetzner-sybren server

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Product Supplier Sync PRO - Test Setup${NC}"
echo -e "${BLUE}========================================${NC}\n"

# 1. Check if we're on the right server
echo -e "${BLUE}[1/8] Checking server...${NC}"
if [ "$(hostname)" != "hetzner-sybren" ]; then
    echo -e "${YELLOW}⚠ Warning: Not on hetzner-sybren server${NC}"
    echo -e "Run this command first: ${GREEN}ssh hetzner-sybren${NC}"
else
    echo -e "${GREEN}✓ On correct server: hetzner-sybren${NC}"
fi

# 2. Check Docker is running
echo -e "\n${BLUE}[2/8] Checking Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is available${NC}"

# 3. Check test supplier containers
echo -e "\n${BLUE}[3/8] Checking test supplier containers...${NC}"
CONTAINERS=(
    "supplier_a_sftp:SFTP Server (port 2222)"
    "supplier_b_http:HTTP Server (port 8000)"
    "supplier_c_api:API Server (port 3000)"
    "supplier_d_db:PostgreSQL DB (port 5432)"
    "supplier_e_xml:XML Server (port 8080)"
)

RUNNING_COUNT=0
for container_info in "${CONTAINERS[@]}"; do
    IFS=':' read -r name desc <<< "$container_info"
    if docker ps --format '{{.Names}}' | grep -q "^${name}$"; then
        echo -e "${GREEN}✓ ${desc} - Running${NC}"
        ((RUNNING_COUNT++))
    else
        echo -e "${RED}✗ ${desc} - Not running${NC}"
        echo -e "  Start with: ${YELLOW}docker start ${name}${NC}"
    fi
done

if [ $RUNNING_COUNT -eq 5 ]; then
    echo -e "${GREEN}✓ All test containers are running${NC}"
else
    echo -e "${YELLOW}⚠ ${RUNNING_COUNT}/5 containers running${NC}"
fi

# 4. Check Odoo container
echo -e "\n${BLUE}[4/8] Checking Odoo container...${NC}"
if docker ps --format '{{.Names}}' | grep -q "odoo19-dev-web-1"; then
    echo -e "${GREEN}✓ Odoo container is running${NC}"
    
    # Get Odoo version
    ODOO_VERSION=$(docker exec odoo19-dev-web-1 odoo --version 2>/dev/null | head -n1 || echo "Unknown")
    echo -e "  Version: ${ODOO_VERSION}"
else
    echo -e "${RED}✗ Odoo container not running${NC}"
    echo -e "  Start with: ${YELLOW}docker start odoo19-dev-web-1${NC}"
fi

# 5. Test network connectivity from Odoo to test servers
echo -e "\n${BLUE}[5/8] Testing network connectivity...${NC}"
if docker ps --format '{{.Names}}' | grep -q "odoo19-dev-web-1"; then
    
    # Test HTTP
    if docker exec odoo19-dev-web-1 curl -s -o /dev/null -w "%{http_code}" http://hetzner-sybren:8000/ 2>/dev/null | grep -q "200\|302"; then
        echo -e "${GREEN}✓ HTTP Server accessible from Odoo${NC}"
    else
        echo -e "${YELLOW}⚠ HTTP Server not accessible from Odoo${NC}"
    fi
    
    # Test API
    if docker exec odoo19-dev-web-1 curl -s -o /dev/null -w "%{http_code}" http://hetzner-sybren:3000/ 2>/dev/null | grep -q "200\|302"; then
        echo -e "${GREEN}✓ API Server accessible from Odoo${NC}"
    else
        echo -e "${YELLOW}⚠ API Server not accessible from Odoo${NC}"
    fi
    
else
    echo -e "${YELLOW}⚠ Odoo not running, skipping connectivity tests${NC}"
fi

# 6. Check if PRO module is installed
echo -e "\n${BLUE}[6/8] Checking module installation...${NC}"
MODULE_PATH="/home/sybren/services/odoo19-dev/data/addons/product_supplier_sync_pro"
if [ -d "$MODULE_PATH" ]; then
    echo -e "${GREEN}✓ PRO module found at ${MODULE_PATH}${NC}"
    
    # Check key files
    if [ -f "$MODULE_PATH/models/import_schedule.py" ]; then
        LINE_COUNT=$(wc -l < "$MODULE_PATH/models/import_schedule.py")
        echo -e "  import_schedule.py: ${LINE_COUNT} lines"
    fi
    
    if [ -f "$MODULE_PATH/__manifest__.py" ]; then
        VERSION=$(grep "version" "$MODULE_PATH/__manifest__.py" | head -n1)
        echo -e "  ${VERSION}"
    fi
else
    echo -e "${RED}✗ PRO module not found${NC}"
fi

# 7. Check Python dependencies in Odoo container
echo -e "\n${BLUE}[7/8] Checking Python dependencies...${NC}"
if docker ps --format '{{.Names}}' | grep -q "odoo19-dev-web-1"; then
    
    DEPS=("paramiko:SFTP" "psycopg2:PostgreSQL" "requests:HTTP/API")
    for dep_info in "${DEPS[@]}"; do
        IFS=':' read -r module desc <<< "$dep_info"
        if docker exec odoo19-dev-web-1 python3 -c "import ${module}" 2>/dev/null; then
            echo -e "${GREEN}✓ ${desc} (${module})${NC}"
        else
            echo -e "${YELLOW}⚠ ${desc} (${module}) - Not installed${NC}"
            echo -e "  Install: ${YELLOW}docker exec odoo19-dev-web-1 pip3 install ${module}${NC}"
        fi
    done
fi

# 8. Quick access info
echo -e "\n${BLUE}[8/8] Quick Access Information${NC}"
echo -e "════════════════════════════════════════"
echo -e "Odoo URL:     ${GREEN}https://dev.sybrendebruijn.nl/odoo${NC}"
echo -e "Database:     ${GREEN}nerbys_dev${NC}"
echo -e "Credentials:  ${GREEN}admin / admin${NC}"
echo -e ""
echo -e "Test Servers (from Odoo container):"
echo -e "  HTTP:       ${GREEN}http://hetzner-sybren:8000${NC}"
echo -e "  API:        ${GREEN}http://hetzner-sybren:3000${NC}"
echo -e "  SFTP:       ${GREEN}hetzner-sybren:2222${NC}"
echo -e "  PostgreSQL: ${GREEN}hetzner-sybren:5432${NC}"
echo -e "  XML:        ${GREEN}http://hetzner-sybren:8080${NC}"
echo -e "════════════════════════════════════════"

# Common Commands
echo -e "\n${BLUE}Useful Commands:${NC}"
echo -e "────────────────────────────────────────"
echo -e "View Odoo logs:"
echo -e "  ${YELLOW}docker logs -f odoo19-dev-web-1${NC}"
echo -e ""
echo -e "Restart Odoo:"
echo -e "  ${YELLOW}docker restart odoo19-dev-web-1${NC}"
echo -e ""
echo -e "Upgrade PRO module:"
echo -e "  ${YELLOW}python3 /home/sybren/scripts/upgrade_module.py dev product_supplier_sync_pro${NC}"
echo -e ""
echo -e "Test HTTP server locally:"
echo -e "  ${YELLOW}curl http://localhost:8000/${NC}"
echo -e ""
echo -e "Enter Odoo container:"
echo -e "  ${YELLOW}docker exec -it odoo19-dev-web-1 /bin/bash${NC}"
echo -e ""
echo -e "Install missing dependencies:"
echo -e "  ${YELLOW}docker exec odoo19-dev-web-1 pip3 install paramiko psycopg2-binary${NC}"
echo -e "────────────────────────────────────────"

echo -e "\n${GREEN}Setup check complete!${NC}"
echo -e "Ready to test scheduled imports in Odoo.\n"
