# Script Path Fixes Summary

This document summarizes the hardcoded path fixes applied to the scripts directory.

## Fixed Files

### Conversion Scripts
1. **convert_maverick_properly.py**
   - Changed: `/Users/polyversai/.lmstudio/mlx_lm` → Uses `MLX_LM_PATH` env var or `~/.lmstudio/mlx_lm`
   - Changed: `/Users/polyversai/.lmstudio/models/` → Uses `LMSTUDIO_MODELS_DIR` env var or `~/.lmstudio/models`

2. **convert_vision_models_properly.sh**
   - Changed: `/Users/polyversai/.lmstudio/` → `~/.lmstudio/`
   - Uses `os.path.expanduser()` for Python paths

3. **fix_vlm_conversion.sh**
   - Changed: All `/Users/polyversai/.lmstudio/` → `~/.lmstudio/`

4. **fix_vlm_timeout.py**
   - Changed: Hardcoded Python path → Auto-detects Python version
   - Uses `MLX_VENV_PATH` env var or auto-detection
   - Changed: All absolute paths → Uses `os.path.expanduser()`

5. **resume_maverick_conversion.sh**
   - Changed: Hardcoded paths → Uses `LMSTUDIO_MODELS_DIR` env var or `~/.lmstudio/models`

### Network Scripts
1. **balanced_network_routing.sh**
   - Changed: `/Users/polyversai/hosted_dev/mlx_lm_servers/` → Dynamic path using `SCRIPT_DIR` and `PROJECT_DIR`

2. **setup_traffic_shaping.sh**
   - Changed: `/Users/polyversai/hosted_dev/mlx_lm_servers/` → Dynamic path using `SCRIPT_DIR` and `PROJECT_DIR`

### Setup Scripts
1. **mlx-llm-server.service**
   - Changed: Hardcoded user paths → Uses systemd specifiers:
     - `%i` for user instance
     - `%h` for home directory
   - Now works for any user when installed as a user service

## Environment Variables

The following environment variables can be used to customize paths:

- `MLX_LM_PATH`: Path to mlx_lm installation (default: `~/.lmstudio/mlx_lm`)
- `LMSTUDIO_MODELS_DIR`: Path to LMStudio models directory (default: `~/.lmstudio/models`)
- `MLX_VENV_PATH`: Path to MLX virtual environment site-packages

## Files Without Changes

The following files were checked and found to have no hardcoded paths:
- `convert-to-mlx-enhanced.sh`
- `network_traffic_policy.conf`
- `configure_network_routing.sh` (uses configurable variables)
- `manage.sh`
- `start_server.sh`
- All files in `testing/` directory

## Recommendations

1. When running the scripts, users can set environment variables to customize paths:
   ```bash
   export MLX_LM_PATH=/custom/path/to/mlx_lm
   export LMSTUDIO_MODELS_DIR=/custom/models/directory
   ```

2. The network routing scripts (configure_network_routing.sh, balanced_network_routing.sh) still contain hardcoded IP addresses and network interfaces. These are specific to the network setup and should be configured by users according to their network topology.

3. Consider creating a `.env.example` file with all configurable paths and network settings for easier setup.