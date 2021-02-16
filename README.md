# timelord
Discord bot for scheduling events, collecting RSVPs and reminding attendees

## Installation

### 1. Clone repository and rename config

```
git clone https://github.com/svenmauch/timelord.git
cd timelord
mv ./timelord/.env.example ./timelord/.env
```

### 2. Edit config file

```
vim ./timelord/.env
```

### 3. Run bot as daemon

```
docker-compose up -d
```