CREATE TABLE IF NOT EXISTS places (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255) COLLATE utf8mb4_bin NOT NULL,
    attribute_code INT NULL,
    shape_code INT NULL,
    lat DECIMAL(10,7) NULL,
    lng DECIMAL(11,7) NULL,
    lat2 DECIMAL(10,7) NULL,
    lng2 DECIMAL(11,7) NULL,
    source TEXT NOT NULL,
    source_detail TEXT NOT NULL,
    notes TEXT NOT NULL,
    INDEX idx_places_name (name)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;

CREATE TABLE IF NOT EXISTS place_aliases (
    id BIGINT PRIMARY KEY,
    place_id BIGINT NOT NULL,
    alias VARCHAR(255) COLLATE utf8mb4_bin NOT NULL,
    alias_type VARCHAR(255) NOT NULL,
    INDEX idx_alias (alias),
    CONSTRAINT fk_alias_place FOREIGN KEY (place_id) REFERENCES places(id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
