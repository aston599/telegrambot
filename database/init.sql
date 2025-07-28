-- 🤖 KirveHub Bot - Database Initialization Script
-- PostgreSQL için optimize edilmiş

-- Database oluştur (eğer yoksa)
-- CREATE DATABASE kirvehub_db;

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users tablosu
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    is_registered BOOLEAN DEFAULT FALSE,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    kirve_points DECIMAL(10,2) DEFAULT 0.00,
    daily_points DECIMAL(10,2) DEFAULT 0.00,
    total_messages INTEGER DEFAULT 0,
    last_point_date DATE DEFAULT CURRENT_DATE,
    rank_level INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Groups tablosu
CREATE TABLE IF NOT EXISTS groups (
    group_id BIGINT PRIMARY KEY,
    group_name VARCHAR(255),
    group_type VARCHAR(50),
    member_count INTEGER DEFAULT 0,
    is_registered BOOLEAN DEFAULT FALSE,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    admin_user_id BIGINT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Daily stats tablosu
CREATE TABLE IF NOT EXISTS daily_stats (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    group_id BIGINT,
    message_date DATE NOT NULL,
    message_count INTEGER DEFAULT 0,
    points_earned DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES groups(group_id) ON DELETE CASCADE,
    UNIQUE(user_id, group_id, message_date)
);

-- Point settings tablosu
CREATE TABLE IF NOT EXISTS point_settings (
    id SERIAL PRIMARY KEY,
    setting_name VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bot status tablosu
CREATE TABLE IF NOT EXISTS bot_status (
    id SERIAL PRIMARY KEY,
    status VARCHAR(50) NOT NULL,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Events tablosu
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    event_name VARCHAR(255) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    description TEXT,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    max_participants INTEGER,
    current_participants INTEGER DEFAULT 0,
    created_by BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Event participants tablosu
CREATE TABLE IF NOT EXISTS event_participants (
    id SERIAL PRIMARY KEY,
    event_id INTEGER NOT NULL,
    user_id BIGINT NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active',
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE(event_id, user_id)
);

-- Market items tablosu
CREATE TABLE IF NOT EXISTS market_items (
    id SERIAL PRIMARY KEY,
    item_name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    item_type VARCHAR(50) NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    stock_quantity INTEGER DEFAULT -1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders tablosu
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1,
    total_price DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES market_items(id) ON DELETE CASCADE
);

-- System logs tablosu
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    log_level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    user_id BIGINT,
    group_id BIGINT,
    additional_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (group_id) REFERENCES groups(group_id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_is_registered ON users(is_registered);
CREATE INDEX IF NOT EXISTS idx_users_kirve_points ON users(kirve_points DESC);
CREATE INDEX IF NOT EXISTS idx_users_last_activity ON users(last_activity);

CREATE INDEX IF NOT EXISTS idx_groups_is_registered ON groups(is_registered);
CREATE INDEX IF NOT EXISTS idx_groups_admin_user_id ON groups(admin_user_id);

CREATE INDEX IF NOT EXISTS idx_daily_stats_user_date ON daily_stats(user_id, message_date);
CREATE INDEX IF NOT EXISTS idx_daily_stats_group_date ON daily_stats(group_id, message_date);

CREATE INDEX IF NOT EXISTS idx_events_active ON events(is_active);
CREATE INDEX IF NOT EXISTS idx_events_dates ON events(start_date, end_date);

CREATE INDEX IF NOT EXISTS idx_event_participants_event ON event_participants(event_id);
CREATE INDEX IF NOT EXISTS idx_event_participants_user ON event_participants(user_id);

CREATE INDEX IF NOT EXISTS idx_market_items_available ON market_items(is_available);
CREATE INDEX IF NOT EXISTS idx_market_items_type ON market_items(item_type);

CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);

CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(log_level);
CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at);

-- Default point settings
INSERT INTO point_settings (setting_name, setting_value, description) VALUES
('point_per_message', '0.04', 'Her mesaj için kazanılan point miktarı'),
('daily_point_limit', '5.00', 'Günlük maksimum point limiti'),
('flood_protection_seconds', '10', 'Flood koruması için bekleme süresi'),
('min_message_length', '5', 'Point kazanmak için minimum mesaj uzunluğu'),
('max_concurrent_updates', '100', 'Maksimum eşzamanlı güncelleme'),
('rate_limit_delay', '0.1', 'Rate limiting için bekleme süresi')
ON CONFLICT (setting_name) DO NOTHING;

-- Default bot status
INSERT INTO bot_status (status, message) VALUES
('started', 'Bot başlatıldı'),
('running', 'Bot çalışıyor'),
('maintenance', 'Bot bakım modunda')
ON CONFLICT DO NOTHING;

-- Functions
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_groups_updated_at BEFORE UPDATE ON groups
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_events_updated_at BEFORE UPDATE ON events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_market_items_updated_at BEFORE UPDATE ON market_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to reset daily points
CREATE OR REPLACE FUNCTION reset_daily_points()
RETURNS void AS $$
BEGIN
    UPDATE users 
    SET daily_points = 0.00, last_point_date = CURRENT_DATE
    WHERE last_point_date < CURRENT_DATE;
END;
$$ LANGUAGE plpgsql;

-- Function to get user statistics
CREATE OR REPLACE FUNCTION get_user_stats(p_user_id BIGINT)
RETURNS TABLE(
    total_points DECIMAL(10,2),
    daily_points DECIMAL(10,2),
    total_messages INTEGER,
    rank_level INTEGER,
    registration_date TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.kirve_points,
        u.daily_points,
        u.total_messages,
        u.rank_level,
        u.registration_date
    FROM users u
    WHERE u.user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO kirvehub;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO kirvehub;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO kirvehub;

-- Vacuum and analyze
VACUUM ANALYZE; 