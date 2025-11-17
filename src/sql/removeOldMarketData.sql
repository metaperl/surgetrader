DELETE FROM market WHERE timestamp <= date('now', '-2 day');
