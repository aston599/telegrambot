-- Market tablolarını güncelleme scripti

-- Market categories tablosuna emoji kolonu ekle
ALTER TABLE IF EXISTS market_categories 
ADD COLUMN IF NOT EXISTS emoji VARCHAR(10);

-- Market products tablosuna yeni kolonlar ekle
ALTER TABLE IF EXISTS market_products 
ADD COLUMN IF NOT EXISTS company_name VARCHAR(255);

ALTER TABLE IF EXISTS market_products 
ADD COLUMN IF NOT EXISTS site_link VARCHAR(500);

-- Stock kolonunu düzelt (eğer stock_quantity yoksa)
ALTER TABLE IF EXISTS market_products 
ADD COLUMN IF NOT EXISTS stock INTEGER DEFAULT -1;

-- Eğer stock_quantity varsa ve stock yoksa, stock_quantity'yi stock'a kopyala
UPDATE market_products 
SET stock = stock_quantity 
WHERE stock IS NULL AND stock_quantity IS NOT NULL;

-- Market kategorilerini ekle
INSERT INTO market_categories (category_name, description, emoji, is_active) VALUES
('gaming', 'Kumar ve oyun siteleri', '🎰', true),
('casino', 'Casino siteleri', '🎲', true),
('sports', 'Spor bahis siteleri', '⚽', true),
('poker', 'Poker siteleri', '🃏', true),
('live', 'Canlı casino', '🎥', true)
ON CONFLICT (category_name) DO NOTHING; 