{
  "apps": [
    {
      "name": "kirvehub-bot",
      "script": "main.py",
      "interpreter": "python",
      "env": {
        "PRODUCTION_MODE": "true",
        "PYTHONPATH": "."
      },
      "instances": 1,
      "autorestart": true,
      "watch": false,
      "max_memory_restart": "200M",
      "error_file": "./logs/pm2_error.log",
      "out_file": "./logs/pm2_out.log",
      "log_file": "./logs/pm2_combined.log",
      "time": true
    }
  ]
}
