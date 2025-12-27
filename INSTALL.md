# Installation Guide

## Prerequisites

### 1. Ollama Server

You need an Ollama server running on your network. Install Ollama on your desired host:

**Linux/MacOS:**
```bash
curl https://ollama.ai/install.sh | sh
```

**Windows:**
Download from [ollama.ai](https://ollama.ai)

Start the Ollama service:
```bash
ollama serve
```

### 2. Download a Compatible Model

For best results, use a tool-capable model:

```bash
ollama pull home-functiongemma-270m
```

Other models may work but might not support function calling properly.

### 3. Verify Ollama is Running

Test the connection:
```bash
curl http://localhost:11434/api/tags
```

You should see a JSON response with your installed models.

## Installation Methods

### Method 1: HACS (Recommended)

1. **Open HACS**
   - Go to Home Assistant → HACS

2. **Add Custom Repository**
   - Click the three dots (⋮) menu
   - Select "Custom repositories"
   - Add URL: `https://github.com/yourusername/homeassistant-ollama-agent`
   - Category: Integration

3. **Install Integration**
   - Search for "Ollama Conversation"
   - Click "Download"
   - Restart Home Assistant

### Method 2: Manual Installation

1. **Download Files**
   ```bash
   cd /config
   mkdir -p custom_components
   cd custom_components
   git clone https://github.com/yourusername/homeassistant-ollama-agent.git
   mv homeassistant-ollama-agent/custom_components/ollama_conversation .
   rm -rf homeassistant-ollama-agent
   ```

2. **Restart Home Assistant**
   - Settings → System → Restart

3. **Verify Installation**
   - Check logs for "Loaded component ollama_conversation"

## Configuration

### Step 1: Add Integration

1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"**
3. Search for **"Ollama Conversation"**

### Step 2: Connect to Ollama

1. **Server URL**: Enter your Ollama server address
   - Local: `http://localhost:11434`
   - Network: `http://sanctuarymoon.local:11434`
   - Custom port: `http://192.168.1.100:11434`

2. Click **Submit**

### Step 3: Select Model

1. **Model**: Choose from the dropdown (detected from your server)
2. **Temperature** (optional): 0.0-2.0 (default: 0.7)
   - Lower = more deterministic
   - Higher = more creative
3. **Context Window** (optional): Token limit (default: 8192)
4. **Top P** (optional): 0.0-1.0 (default: 0.9)
5. **Top K** (optional): Integer (default: 40)

3. Click **Submit**

### Step 4: Test the Integration

1. Go to **Developer Tools** → **Services**
2. Select service: `conversation.process`
3. YAML:
   ```yaml
   text: "Turn on the kitchen lights"
   agent_id: conversation.ollama_conversation
   ```
4. Click **Call Service**

## Troubleshooting Installation

### "Cannot connect to Ollama server"

**Check Server Running:**
```bash
systemctl status ollama  # Linux
ps aux | grep ollama      # Any OS
```

**Test Connection:**
```bash
curl http://YOUR_SERVER:11434/api/tags
```

**Common Issues:**
- Firewall blocking port 11434
- Wrong IP address or hostname
- Ollama not started
- Network connectivity issues

### "No models found on the server"

**List Models:**
```bash
ollama list
```

**Pull a Model:**
```bash
ollama pull home-functiongemma-270m
```

### Integration Not Appearing

1. **Check Logs:**
   - Settings → System → Logs
   - Filter for "ollama"

2. **Verify Files:**
   ```bash
   ls -la /config/custom_components/ollama_conversation/
   ```

3. **Clear Cache:**
   - Delete `/config/.storage/core.config_entries` (backup first!)
   - Restart Home Assistant

## Upgrading

### HACS Upgrade

1. HACS → Integrations
2. Find "Ollama Conversation"
3. Click "Update"
4. Restart Home Assistant

### Manual Upgrade

1. Backup current installation
2. Delete old files:
   ```bash
   rm -rf /config/custom_components/ollama_conversation
   ```
3. Follow manual installation steps
4. Restart Home Assistant
5. Existing configuration will be preserved

## Uninstallation

1. **Remove Integration:**
   - Settings → Devices & Services
   - Find "Ollama Conversation"
   - Click three dots → Delete

2. **Remove Files:**
   ```bash
   rm -rf /config/custom_components/ollama_conversation
   ```

3. **Restart Home Assistant**

## Next Steps

- [Usage Examples](custom_components/ollama_conversation/README.md#usage-examples)
- [Configuration Options](custom_components/ollama_conversation/README.md#configuration)
- [Troubleshooting Guide](custom_components/ollama_conversation/README.md#troubleshooting)
