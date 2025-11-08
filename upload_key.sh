#!/bin/bash
echo "Uploading SSH key to NAS..."
cat ~/.ssh/nas_key.pub | ssh vs_code@192.168.178.43 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
echo "Key uploaded successfully!"
