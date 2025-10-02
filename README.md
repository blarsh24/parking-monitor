# ACE Parking Monitor 🚗

Automated monitoring system for ACE Parking availability with Discord notifications.

## Features

- 🔍 Monitors parking availability every 5 minutes
- 🔔 Discord notifications when parking becomes available
- 🛡️ Robust error handling and retry logic
- 📊 State persistence between runs
- 🧪 Local testing capabilities
- 🚀 Fully automated with GitHub Actions

## Target Parking

- **Site**: Samuel Merritt University Fall 2025 Parking
- **URL**: [ACE Parking Reserve Page](https://space.aceparking.com/site/reserve/4fac9ba115140ac4f1c22da82aa0bc7f)
- **Price**: $67.45
- **Current Status**: Monitoring for availability

## Quick Start

### 1. Fork This Repository

Click the "Fork" button at the top right of this repository.

### 2. Set Up Discord Webhook

1. Open Discord and go to your server
2. Go to Server Settings → Integrations → Webhooks
3. Click "New Webhook"
4. Name it "Parking Monitor"
5. Select the channel for notifications
6. Copy the webhook URL

### 3. Add GitHub Secret

1. Go to your forked repository
2. Click Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `DISCORD_WEBHOOK_URL`
5. Value: Paste your Discord webhook URL
6. Click "Add secret"

### 4. Enable GitHub Actions

1. Go to the "Actions" tab in your repository
2. Click "I understand my workflows, go ahead and enable them"
3. The monitor will start running automatically every 5 minutes

### 5. Manual Testing

To test the system immediately:
1. Go to Actions tab
2. Select "ACE Parking Monitor"
3. Click "Run workflow"
4. Click "Run workflow" button

## Local Development

### Prerequisites

- Python 3.11+
- pip

### Setup

1. Clone your fork:
```bash
git clone https://github.com/YOUR_USERNAME/parking-monitor.git
cd parking-monitor